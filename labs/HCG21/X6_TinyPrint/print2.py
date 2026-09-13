#!/usr/bin/env python3
# X6 TinyPrint - print text/images on the X6h "cat printer" over Bluetooth LE.
# Copyright (C) 2026 Home Computer Group
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.

"""print2.py - X6h driver that follows TiMini-Print's wire behaviour.

Variant of print.py whose print pipeline mirrors the "tiny" protocol family of
TiMini-Print (github.com/Dejniel/TiMini-Print) for the X6h profile, so a job is
built exactly like that driver:

  * command order: blackening (0xA4) -> energy (0xAF) -> print mode (0xBE)
    -> feed/speed (0xBD) -> scanlines -> end-of-page feed (0xBD), paper
    position (0xA1) x2, feed (0xBD), device state (0xA3);
  * scanlines use the tiny RLE opcode 0xBF when not longer than the raw form,
    otherwise the raw opcode 0xA2 (LSB-first packing);
  * a feed/speed packet is re-issued every 200 scanlines;
  * the job is streamed one scanline per BLE write, paced with a short delay
    (0xAE flow-control notifications are honored if the printer ever sends
    them, but the X6h does not; hence the explicit pacing).

The only deliberate difference from TiMini-Print is the state handling: the
0xA3 reply payload is decoded like in print.py (paper-out flag, battery
voltage) and a no-paper condition aborts the job.

Examples:
    ./catprint2.sh "Hello world"
    ./catprint2.sh "Receipt no.1" --align center --font bold
    echo "line 1" | ./catprint2.sh
    ./catprint2.sh --image photo.jpg
    ./catprint2.sh --list
"""

import argparse
import asyncio
import os
import sys
import time

from PIL import Image, ImageDraw, ImageFont, ImageOps

try:
    from bleak import BleakClient, BleakScanner
except ImportError:
    sys.exit("Missing 'bleak'. Install dependencies with: pip install -r requirements.txt")

# --- tiny protocol (TiMini-Print compatible) ------------------------------

MAGIC = b"\x51\x78"
CMD_RETRACT = 0xA0      # manual retract: 30 00 (200 dpi) / 48 00 (300 dpi)
CMD_PAPER = 0xA1        # paper position / manual feed: 30 00 (200 dpi) / 48 00 (300 dpi)
CMD_RASTER = 0xA2       # raw scanline, LSB-first
CMD_STATE = 0xA3        # device state query/reply
CMD_BLACKENING = 0xA4   # payload 0x30 + level (1..5)
CMD_ENERGY = 0xAF       # payload uint16 LE
CMD_NOTIFY = 0xAE       # buffer notification (payload 0x10 pause / 0x00 resume)
CMD_SPEED = 0xBD        # feed/speed, payload = speed byte
CMD_MODE = 0xBE         # print mode: 1 text / 0 image
CMD_RASTER_RLE = 0xBF   # run-length encoded scanline

FLOW_PAUSE = b"\x51\x78\xae\x01\x01\x00\x10\x70\xff"
FLOW_RESUME = b"\x51\x78\xae\x01\x01\x00\x00\x00\xff"

# TiMini-Print profiles matching an advertised "X6h*" name.
# "d1" is the profile TiMini resolves for the exact name "X6h" (exact/case
# preserved: lowercase "X6h" -> pocket_printer/d1, uppercase "X6H" -> x6h).
PROFILES = {
    "d1": {"image": 5000, "text": 8000},
    "x6h": {"image": 9500, "text": 9500},
}

STREAM_CHUNK_CAP = 512
# The X6h does not emit 0xAE flow-control notifications, so scanlines are paced
# explicitly: one BLE write per scanline plus a short delay.
DEFAULT_ROW_DELAY = 0.035
LINE_FEED_EVERY = 200

SERVICE_UUID = "0000ae30-0000-1000-8000-00805f9b34fb"
TX_UUID = "0000ae01-0000-1000-8000-00805f9b34fb"
RX_UUID = "0000ae02-0000-1000-8000-00805f9b34fb"

PAPER_WIDTH = 384
DEFAULT_NAME = "X6h-0000"

FONTS = {
    "regular": "/System/Library/Fonts/Supplemental/Arial.ttf",
    "bold": "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "mono": "/System/Library/Fonts/Supplemental/Courier New.ttf",
    "mono-bold": "/System/Library/Fonts/Supplemental/Courier New Bold.ttf",
    "menlo": "/System/Library/Fonts/Menlo.ttc",
    "verdana": "/System/Library/Fonts/Supplemental/Verdana.ttf",
    "georgia": "/System/Library/Fonts/Supplemental/Georgia.ttf",
}

ZX_FONT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zx82.ch8")


def crc8(data):
    crc = 0
    for byte in bytes(data):
        crc ^= byte
        for _ in range(8):
            crc = ((crc << 1) ^ 0x07) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc


def reverse_bits(byte):
    byte = ((byte & 0xAA) >> 1) | ((byte & 0x55) << 1)
    byte = ((byte & 0xCC) >> 2) | ((byte & 0x33) << 2)
    return ((byte & 0xF0) >> 4) | ((byte & 0x0F) << 4)


def command(cmd, payload=b""):
    payload = bytes(payload)
    if len(payload) > 0xFF:
        raise ValueError("payload too large (%d > 255)" % len(payload))
    return (MAGIC + bytes([cmd, 0x00, len(payload), 0x00]) + payload
            + bytes([crc8(payload)]) + b"\xff")


def paper_payload(dpi):
    """TiMini-Print's _paper_payload: 200 dpi -> 30 00, 300 dpi -> 48 00."""
    return b"\x48\x00" if int(dpi) == 300 else b"\x30\x00"


def feed_cmd(dpi=200):
    return command(CMD_PAPER, paper_payload(dpi))


def retract_cmd(dpi=200):
    return command(CMD_RETRACT, paper_payload(dpi))


class PacketDecoder:
    """Split a prefixed byte stream into (opcode, flags, payload) packets."""

    def __init__(self):
        self._buffer = bytearray()

    def feed(self, data):
        self._buffer.extend(data)
        packets = []
        while True:
            marker = self._buffer.find(MAGIC)
            if marker < 0:
                keep = 1 if self._buffer[-1:] == MAGIC[:1] else 0
                del self._buffer[:len(self._buffer) - keep]
                break
            if marker:
                del self._buffer[:marker]
            if len(self._buffer) < 6:
                break
            length = self._buffer[4] | (self._buffer[5] << 8)
            total = 6 + length + 2
            if len(self._buffer) < total:
                break
            raw = bytes(self._buffer[:total])
            payload = raw[6:6 + length]
            if raw[-1] != 0xFF or crc8(payload) != raw[-2]:
                del self._buffer[0]
                continue
            packets.append((raw[2], raw[3], payload))
            del self._buffer[:total]
        return packets


def _emit_run(out, color, count):
    while count > 127:
        out.append(((color << 7) | 127) & 0xFF)
        count -= 127
    if count > 0:
        out.append(((color << 7) | count) & 0xFF)


def rle_encode_row(row, width):
    """RLE-encode one scanline (same runs as TiMini-Print's tiny_rle)."""
    out = bytearray()
    if width <= 0:
        return bytes(out)
    prev = (row[0] >> 7) & 1
    count = 1
    for i in range(1, width):
        bit = (row[i >> 3] >> (7 - (i & 7))) & 1
        if bit == prev:
            count += 1
        else:
            _emit_run(out, prev, count)
            prev = bit
            count = 1
    _emit_run(out, prev, count)
    return bytes(out)


def build_scanline_packets(rows, width, width_bytes, height, speed):
    out = bytearray()
    for packet in build_scanline_segments(rows, width, width_bytes, height, speed):
        out += packet
    return bytes(out)


def build_scanline_segments(rows, width, width_bytes, height, speed):
    """Yield one Qx packet per scanline (plus every 200th line feed)."""
    segments = []
    for row in range(height):
        line = rows[row * width_bytes:(row + 1) * width_bytes]
        rle = rle_encode_row(line, width)
        if len(rle) <= width_bytes:
            segments.append(command(CMD_RASTER_RLE, rle))
        else:
            segments.append(command(CMD_RASTER, bytes(reverse_bits(b) for b in line)))
        if LINE_FEED_EVERY and (row + 1) % LINE_FEED_EVERY == 0:
            segments.append(command(CMD_SPEED, bytes([speed & 0xFF])))
    return segments


def build_job_segments(rows, width, *, is_text, energy, speed, blackening, feed_padding,
                       dev_dpi, post_feed):
    """Split the job in (header, scanlines, trailer) so scanlines can be paced."""
    width_bytes = (width + 7) // 8
    height = len(rows) // width_bytes if width_bytes else 0

    header = bytearray()
    header += command(CMD_BLACKENING, bytes([0x30 + max(1, min(5, int(blackening)))]))
    header += command(CMD_ENERGY, int(energy).to_bytes(2, "little"))
    header += command(CMD_MODE, bytes([1 if is_text else 0]))
    header += command(CMD_SPEED, bytes([speed & 0xFF]))

    lines = build_scanline_segments(rows, width, width_bytes, height, speed)

    trailer = bytearray()
    trailer += command(CMD_SPEED, bytes([feed_padding & 0xFF]))
    paper = paper_payload(dev_dpi)
    for _ in range(max(0, int(post_feed))):
        trailer += command(CMD_PAPER, paper)
    trailer += command(CMD_SPEED, bytes([feed_padding & 0xFF]))
    trailer += command(CMD_STATE, b"\x00")
    return bytes(header), lines, bytes(trailer)


def build_job(rows, width, *, is_text, energy, speed, blackening, feed_padding,
              dev_dpi, post_feed):
    """Build the whole print job, byte-compatible with TiMini-Print's X6h job."""
    header, lines, trailer = build_job_segments(
        rows, width, is_text=is_text, energy=energy, speed=speed,
        blackening=blackening, feed_padding=feed_padding, dev_dpi=dev_dpi,
        post_feed=post_feed)
    return header + b"".join(lines) + trailer


# --- content rendering ----------------------------------------------------

def load_font(family, size):
    path = FONTS.get(family, family)
    if not os.path.exists(path):
        raise SystemExit("Font not found: %s" % path)
    return ImageFont.truetype(path, size)


def wrap_text(draw, text, font, max_width):
    lines = []
    for paragraph in text.splitlines():
        if not paragraph:
            lines.append("")
            continue
        words = paragraph.split(" ")
        current = ""
        for word in words:
            trial = word if not current else current + " " + word
            if draw.textlength(trial, font=font) <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                while draw.textlength(word, font=font) > max_width and len(word) > 1:
                    cut = len(word)
                    while cut > 1 and draw.textlength(word[:cut], font=font) > max_width:
                        cut -= 1
                    lines.append(word[:cut])
                    word = word[cut:]
                current = word
        lines.append(current)
    return lines


def render_text(text, font_family, font_size, align, width, line_spacing,
                margin_x, margin_y):
    font = load_font(font_family, font_size)
    probe = Image.new("L", (width, 8), 255)
    draw = ImageDraw.Draw(probe)
    lines = wrap_text(draw, text, font, width - 2 * margin_x)

    ascent, descent = font.getmetrics()
    line_height = ascent + descent
    gap = int(line_height * (line_spacing - 1))
    total_h = margin_y * 2 + max(1, len(lines)) * line_height + max(0, len(lines) - 1) * gap

    img = Image.new("L", (width, total_h), 255)
    draw = ImageDraw.Draw(img)
    y = margin_y
    for line in lines:
        if align != "left":
            line_w = draw.textlength(line, font=font)
            x = int((width - line_w) / 2) if align == "center" else int(width - line_w - margin_x)
        else:
            x = margin_x
        draw.text((x, y), line, font=font, fill=0)
        y += line_height + gap
    return img


def to_bw_image(img, dither=False):
    """Return a 1-bit image where bit 1 = black dot (ink), MSB = leftmost."""
    if img.mode != "L":
        img = img.convert("L")
    if dither:
        return ImageOps.invert(img.convert("1", dither=Image.Dither.FLOYDSTEINBERG))
    return img.point(lambda p: 255 if p < 128 else 0).convert(
        "1", dither=Image.Dither.NONE)


def load_zx_font():
    with open(ZX_FONT_FILE, "rb") as fh:
        return fh.read()


def render_zx_text(text, width, cols=32, margin=0, align="left"):
    font = load_zx_font()
    native = cols * 8
    lines = []
    for raw in text.splitlines():
        if raw == "":
            lines.append("")
            continue
        while len(raw) > cols:
            lines.append(raw[:cols])
            raw = raw[cols:]
        lines.append(raw)
    height = max(1, len(lines)) * 8
    img = Image.new("L", (native, height), 255)
    px = img.load()
    for li, line in enumerate(lines):
        x0 = 0
        if align != "left":
            used = len(line) * 8
            x0 = (native - used) // 2 if align == "center" else native - used
        y0 = li * 8
        for ci, ch in enumerate(line):
            code = ord(ch)
            if not 32 <= code <= 127:
                code = 32
            off = (code - 32) * 8
            for row in range(8):
                bits = font[off + row]
                if not bits:
                    continue
                for col in range(8):
                    if bits & (0x80 >> col):
                        px[x0 + ci * 8 + col, y0 + row] = 0
    factor = width / native
    return img.resize((width, max(1, round(height * factor))), Image.NEAREST)


def prepare_image(path, width):
    img = Image.open(path).convert("L")
    ratio = width / img.width
    return img.resize((width, max(1, int(img.height * ratio))), Image.LANCZOS)


def prepare_zx_screen(path, width):
    img = Image.open(path).convert("L").resize((256, 192), Image.NEAREST)
    return img.resize((width, max(1, round(192 * width / 256))), Image.NEAREST)


def build_test_image(width):
    height = 280
    img = Image.new("L", (width, height), 255)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 8, width - 1, 68], fill=0)
    for x in range(width):
        d.line([x, 84, x, 140], fill=int(255 * x / width))
    font = load_font("regular", 30)
    d.text((8, 150), "CATPRINT X6h (TiMini mode)", font=font, fill=0)
    d.text((8, 190), "print head test ok", font=font, fill=0)
    d.text((8, 230), "abc ABC 123 aeiou", font=font, fill=0)
    d.rectangle([0, height - 18, width - 1, height - 1], fill=0)
    return img


# --- BLE driver -----------------------------------------------------------

class Printer:
    def __init__(self, client, verbose=False, row_delay=DEFAULT_ROW_DELAY):
        self.client = client
        self.verbose = verbose
        self.row_delay = row_delay
        self._paused = False
        self._decoder = PacketDecoder()
        self.state = None
        self.pauses = 0
        self.resumes = 0
        self.max_pause_wait = 0.0
        self.notify_uuids = []
        self._max_write = None

    def _on_notify(self, _char, data):
        payload = bytes(data)
        for opcode, flags, body in self._decoder.feed(payload):
            if opcode == CMD_NOTIFY and flags == 1:
                if body == b"\x10":
                    self._paused = True
                    self.pauses += 1
                    if self.verbose:
                        print("  flow: PAUSE", file=sys.stderr)
                elif body == b"\x00":
                    self._paused = False
                    self.resumes += 1
                    if self.verbose:
                        print("  flow: resume", file=sys.stderr)
            elif opcode == CMD_STATE:
                self.state = body
                self._report_state(body)
            elif self.verbose and body:
                print("  notify: %s (op=%02X flags=%02X)" % (payload.hex(), opcode, flags),
                      file=sys.stderr)

    def _report_state(self, state):
        if not self.verbose or len(state) < 3:
            return
        paper = "OUT" if state[1] & 0x10 else "ok"
        print("  state: flags=0x%02X battery=%d.%d V paper=%s"
              % (state[1], state[2] // 10, state[2] % 10, paper), file=sys.stderr)

    async def start(self):
        """Subscribe to the printer's notify characteristic (ae02)."""
        self.notify_uuids = []
        try:
            await self.client.start_notify(RX_UUID, self._on_notify)
            self.notify_uuids.append(RX_UUID)
        except Exception as exc:  # noqa: BLE001
            if self.verbose:
                print("  notify subscribe failed %s: %s" % (RX_UUID, exc), file=sys.stderr)
        if self.verbose:
            print("  subscribed: %s" % ", ".join(self.notify_uuids), file=sys.stderr)

    def _resolve_max_write(self):
        """Largest single ATT write-without-response payload accepted by the printer."""
        if self._max_write:
            return self._max_write
        size = 182
        try:
            char = self.client.services.get_characteristic(TX_UUID)
            reported = getattr(char, "max_write_without_response_size", None)
            if isinstance(reported, int) and reported > 0:
                size = min(reported, STREAM_CHUNK_CAP)
        except Exception:
            pass
        self._max_write = max(1, size)
        return self._max_write

    async def _write(self, data):
        if self._paused:
            started = time.monotonic()
            while self._paused:
                await asyncio.sleep(0.005)
            self.max_pause_wait = max(self.max_pause_wait, time.monotonic() - started)
        limit = self._resolve_max_write()
        for offset in range(0, len(data), limit):
            await self.client.write_gatt_char(TX_UUID, data[offset:offset + limit], response=False)

    async def _send_job(self, header, lines, trailer):
        await self._write(header)
        for segment in lines:
            await self._write(segment)
            if self.row_delay:
                await asyncio.sleep(self.row_delay)
        await self._write(trailer)

    async def get_device_state(self):
        await self._write(command(CMD_STATE, b"\x00"))

    async def read_state(self, tries=20):
        """Query the printer state and return its payload, or None."""
        self.state = None
        await self.get_device_state()
        for _ in range(tries):
            if self.state is not None:
                return self.state
            await asyncio.sleep(0.05)
        return None

    async def print_bitmap(self, rows, width, *, is_text, energy, speed, blackening,
                           feed_padding, dev_dpi, post_feed):
        header, lines, trailer = build_job_segments(
            rows, width, is_text=is_text, energy=energy, speed=speed,
            blackening=blackening, feed_padding=feed_padding, dev_dpi=dev_dpi,
            post_feed=post_feed)
        if self.verbose:
            print("  %d scanlines, row delay %.1f ms"
                  % (len(lines), self.row_delay * 1000), file=sys.stderr)
        await self._send_job(header, lines, trailer)

    async def feed(self, dpi=200):
        """Manual paper advance (TiMini-Print ConnectedPrinter.feed)."""
        await self._write(feed_cmd(dpi))

    async def retract(self, dpi=200):
        """Manual paper retract (TiMini-Print ConnectedPrinter.retract)."""
        await self._write(retract_cmd(dpi))


# --- scanning / connection ------------------------------------------------

async def find_device(name):
    print("Scanning Bluetooth...", file=sys.stderr)
    device = await BleakScanner.find_device_by_name(name, timeout=15)
    if device is not None:
        return device
    devices = await BleakScanner.discover(timeout=8)
    for dev in devices:
        dev_name = (dev.name or "").lower()
        if any(k in dev_name for k in ("x6", "x5", "x7", "print", "cat", "gb0", "gt0", "mx0")):
            print("Using device: %s" % dev.name, file=sys.stderr)
            return dev
    return None


async def list_devices():
    devices = await BleakScanner.discover(timeout=10)
    for dev in sorted(devices, key=lambda d: (d.name or "~")):
        print("%-40s %s" % (dev.address, dev.name or "(no name)"))


def pretty_ascii(data):
    out, cur = [], ""
    for b in bytes(data):
        if 32 <= b < 127:
            cur += chr(b)
        else:
            if len(cur) >= 3:
                out.append(cur)
            cur = ""
    if len(cur) >= 3:
        out.append(cur)
    return out


async def show_info(args):
    """Connect to the printer and read its status (state payload is decoded)."""
    target = args.address or await find_device(args.device)
    if target is None:
        raise SystemExit(
            "Printer '%s' not found. Is it on and NOT already connected "
            "to the phone app? (BLE allows one connection at a time)" % args.device)
    replies = []

    async with BleakClient(target, timeout=30) as client:
        print("Connected to %s" % args.device)
        for service in client.services:
            print("  service %s" % service.uuid)
        await client.start_notify(RX_UUID, lambda _c, d: replies.append(bytes(d)))
        await asyncio.sleep(0.4)
        for label, cmd, payload in (("state", CMD_STATE, b"\x00"),
                                    ("info", 0xA8, b"\x00")):
            await client.write_gatt_char(TX_UUID, command(cmd, payload), response=False)
            await asyncio.sleep(0.6)
            raw = " ".join(r.hex() for r in replies) or "(no reply)"
            print("  %-8s -> %s" % (label, raw))
            for report in replies:
                body = bytes(report)[6:-2]
                if not body:
                    continue
                print("  %-8s    payload: %s" % ("", body.hex(" ")))
                if cmd == CMD_STATE and len(body) >= 3:
                    paper = "OUT" if body[1] & 0x10 else "ok"
                    print("  %-8s    counter=%d  flags=0x%02X  paper=%s"
                          % ("", body[0], body[1], paper))
                    volts = body[2]
                    bars = (5 if volts >= 41 else 4 if volts >= 39 else
                            3 if volts >= 38 else 2 if volts >= 37 else
                            1 if volts >= 35 else 0)
                    print("  %-8s    battery=%d.%d V (%d/5)"
                          % ("", volts // 10, volts % 10, bars))
            for text in pretty_ascii(b"".join(replies)):
                print("  %-8s    text: %r" % ("", text))
            replies.clear()
        if args.delay:
            await asyncio.sleep(args.delay)


async def connect_client(args):
    """Connect to the printer, retrying like print.py."""
    device_name = args.device
    last_error = None
    for attempt in range(1, args.retries + 1):
        target = args.address or await find_device(device_name)
        if target is None:
            print("Attempt %d: printer not found" % attempt, file=sys.stderr)
        else:
            try:
                client = BleakClient(target, timeout=30)
                await client.connect()
                return client
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                print("Attempt %d: connection failed (%s)" % (attempt, exc),
                      file=sys.stderr)
        if attempt < args.retries:
            await asyncio.sleep(2)
    raise SystemExit("Cannot connect to '%s'%s" % (
        device_name, ": %s" % last_error if last_error else ""))


async def paper_motion(args):
    """Send a single manual FEED (0xA1) or RETRACT (0xA0) packet."""
    client = await connect_client(args)
    try:
        printer = Printer(client, verbose=args.verbose)
        await printer.start()
        await asyncio.sleep(0.5)
        if args.retract:
            await printer.retract(args.dpi)
        else:
            await printer.feed(args.dpi)
        await asyncio.sleep(0.3)
        if args.delay:
            await asyncio.sleep(args.delay)
    finally:
        try:
            await client.disconnect()
        except Exception:  # noqa: BLE001
            pass
    print("Retract" if args.retract else "Feed")


async def run(args):
    if args.info:
        await show_info(args)
        return
    if args.feed or args.retract:
        await paper_motion(args)
        return
    text = ""
    if args.file:
        text = open(args.file, "r", encoding="utf-8").read()
    elif args.text:
        text = " ".join(args.text)
    elif not sys.stdin.isatty():
        text = sys.stdin.read()

    is_text = bool(text) and not args.image and not args.test

    if args.test:
        img = build_test_image(args.width)
    elif args.image:
        if args.zx_screen:
            img = prepare_zx_screen(args.image, args.width)
        else:
            img = prepare_image(args.image, args.width)
    elif text:
        if args.font == "zx":
            img = render_zx_text(text, args.width, args.zx_cols, args.margin, args.align)
        else:
            img = render_text(text, args.font, args.font_size, args.align, args.width,
                              args.line_spacing, args.margin, args.margin_v)
    else:
        raise SystemExit("No text. Use --help.")

    invert = args.invert if args.invert is not None else args.zx_screen
    if invert:
        img = ImageOps.invert(img.convert("L"))

    vscale = 1.0 if args.zx_screen else args.vscale
    if vscale != 1.0:
        img = img.resize((img.width, max(1, round(img.height * vscale))),
                         Image.LANCZOS)

    dither = args.dither and bool(args.image)
    bw = to_bw_image(img, dither)
    width = bw.width
    height = bw.height
    rows = bw.tobytes()

    if args.dry_run:
        out = args.dry_run if args.dry_run.endswith(".pbm") else args.dry_run + ".pbm"
        with open(out, "wb") as fh:
            fh.write(b"P4\n%d %d\n" % (width, height) + rows)
        print("Preview saved to %s (%dx%d)" % (out, width, height))
        return

    profile = PROFILES[args.profile]
    energy = args.energy if args.energy is not None else profile["text" if is_text else "image"]

    device_name = args.device
    client = await connect_client(args)

    try:
        printer = Printer(client, verbose=args.verbose, row_delay=args.row_delay)
        await printer.start()
        await asyncio.sleep(0.5)

        state = await printer.read_state()
        if state is None:
            print("Warning: no state reply from the printer", file=sys.stderr)
        else:
            flags = state[1] if len(state) > 1 else 0
            level = state[2] if len(state) > 2 else -1
            if args.verbose:
                print("  state: flags=0x%02X level=%d" % (flags, level),
                      file=sys.stderr)
            if flags & 0x10:
                raise SystemExit("Printer reports NO PAPER. Load paper and retry.")

        await printer.print_bitmap(rows, width, is_text=is_text, energy=energy,
                                   speed=args.speed, blackening=args.blackening,
                                   feed_padding=args.feed_padding, dev_dpi=args.dpi,
                                   post_feed=args.post_feed)
        if args.verbose:
            print("  flow: %d pauses, %d resumes, max wait %.2f s"
                  % (printer.pauses, printer.resumes, printer.max_pause_wait),
                  file=sys.stderr)
        await asyncio.sleep(1.0)
        if args.delay:
            await asyncio.sleep(args.delay)
    finally:
        try:
            await client.disconnect()
        except Exception:  # noqa: BLE001
            pass
    print("Sent to %s" % device_name)


def build_parser():
    p = argparse.ArgumentParser(
        description="Print text/images on the X6h over BLE, using TiMini-Print's "
                    "tiny protocol behaviour (state payload still decoded).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("text", nargs="*", help="text to print")
    p.add_argument("-f", "--file", help="read the text from a file")
    p.add_argument("--image", help="print an image (png/jpg/...)")
    p.add_argument("--test", action="store_true",
                   help="print a test page (black bands, gradient, text)")
    p.add_argument("--device", default=DEFAULT_NAME, help="printer Bluetooth name")
    p.add_argument("--address", help="device address/UUID (skips scanning)")
    p.add_argument("--list", action="store_true", help="list BLE devices and exit")
    p.add_argument("--info", action="store_true",
                   help="connect and read printer status/info, then exit")
    paper = p.add_mutually_exclusive_group()
    paper.add_argument("--feed", action="store_true",
                       help="advance paper a step (0xA1) and exit")
    paper.add_argument("--retract", action="store_true",
                       help="retract paper a step (0xA0) and exit")
    p.add_argument("--font", default="regular", choices=sorted(set(FONTS) | {"zx"}),
                   help="font ('zx' = ZX Spectrum font)")
    p.add_argument("--zx-cols", type=int, default=32,
                   help="characters per line with the ZX font (ZX screen = 32)")
    grp = p.add_mutually_exclusive_group()
    grp.add_argument("--invert", action="store_true", dest="invert", default=None,
                     help="invert (white on black)")
    grp.add_argument("--no-invert", action="store_false", dest="invert",
                     help="do not invert, even in --zx-screen mode")
    p.add_argument("--font-size", type=int, default=32, help="font size in points")
    p.add_argument("--align", default="left", choices=["left", "center", "right"])
    p.add_argument("--width", type=int, default=PAPER_WIDTH, help="printhead width in pixels")
    p.add_argument("--vscale", type=float, default=1.0,
                   help="vertical scale compensation (1.0 = real proportions)")
    p.add_argument("--line-spacing", type=float, default=1.15, help="line spacing")
    p.add_argument("--margin", type=int, default=8, help="horizontal margin in pixels")
    p.add_argument("--margin-v", type=int, default=8, help="vertical margin in pixels")
    p.add_argument("--profile", default="d1", choices=sorted(PROFILES),
                   help="TiMini-Print profile for the X6h (d1 = advertised 'X6h')")
    p.add_argument("--energy", type=int, default=None,
                   help="raw thermal energy, overrides --profile defaults")
    p.add_argument("--blackening", type=int, default=3, choices=range(1, 6),
                   help="dot blackening level 1-5 (0xA4)")
    p.add_argument("--speed", type=int, default=1, help="motor speed (0xBD)")
    p.add_argument("--dpi", type=int, default=200, choices=(200, 300),
                   help="paper DPI for the 0xA1 command")
    p.add_argument("--feed-padding", type=int, default=12,
                   help="final feed value (0xBD) before/after the paper commands")
    p.add_argument("--post-feed", type=int, default=2,
                   help="number of paper-position (0xA1) packets at end of page")
    p.add_argument("--row-delay", type=float, default=DEFAULT_ROW_DELAY,
                   help="pause between scanlines in seconds (pacing)")
    p.add_argument("--retries", type=int, default=4, help="connection attempts")
    p.add_argument("--delay", type=float, default=0.0,
                   help="seconds to wait before disconnecting the printer")
    p.add_argument("--no-dither", action="store_false", dest="dither",
                   help="disable dithering (on by default for images)")
    p.add_argument("--zx-screen", action="store_true",
                   help="treat the image as a ZX 256x192 screen (inverted, 1:1 pixels)")
    p.add_argument("--dry-run", metavar="FILE.pbm", help="only generate the preview, do not print")
    p.add_argument("-v", "--verbose", action="store_true", help="show printer notifications")
    return p


def main():
    args = build_parser().parse_args()
    if args.list:
        asyncio.run(list_devices())
        return 0
    asyncio.run(run(args))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
