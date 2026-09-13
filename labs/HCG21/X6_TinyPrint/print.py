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

"""print.py - Print text (and images) on the "cat printer" X6h thermal printer
(Tiny Print app) over Bluetooth Low Energy.

The device does not speak ESC/POS: it receives monochrome bitmaps using a
proprietary "Qx" protocol. This program:
  1. renders the text to a 1-bit image as wide as the printhead (384 px),
  2. sends it scanline by scanline using the Qx protocol over BLE (bleak),
  3. handles flow control (the printer notifies when its buffer is full).

Examples:
    ./catprint.sh "Hello world"
    ./catprint.sh "Receipt no.1" --align center --font bold --font-size 36
    echo "line 1\nline 2" | ./catprint.sh
    ./catprint.sh --image photo.jpg
    ./catprint.sh --list
"""

import argparse
import asyncio
import os
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps

try:
    from bleak import BleakClient, BleakScanner
except ImportError:
    sys.exit("Missing 'bleak'. Install dependencies with: pip install -r requirements.txt")

# --- Qx protocol ----------------------------------------------------------

MAGIC = b"\x51\x78"
CMD_FEED = 0xA1
CMD_BITMAP = 0xA2
CMD_STATE = 0xA3
CMD_DPI = 0xA4
CMD_LATTICE = 0xA6
CMD_UPDATE = 0xA9
CMD_ENERGY = 0xAF
CMD_SPEED = 0xBD
CMD_APPLY_ENERGY = 0xBE

START_LATTICE = bytes([0xAA, 0x55, 0x17, 0x38, 0x44, 0x5F, 0x5F, 0x5F, 0x44, 0x38, 0x2C])
END_LATTICE = bytes([0xAA, 0x55, 0x17, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x17])

FLOW_PAUSE = b"\x51\x78\xae\x01\x01\x00\x10\x70\xff"
FLOW_RESUME = b"\x51\x78\xae\x01\x01\x00\x00\x00\xff"

# Strength 1-7 -> (thermal energy, per-row delay in seconds)
STRENGTH_ENERGY = {1: 8000, 2: 11000, 3: 14500, 4: 18500, 5: 22500, 6: 26500, 7: 30000}
STRENGTH_DELAY = {1: 0.010, 2: 0.012, 3: 0.014, 4: 0.016, 5: 0.019, 6: 0.022, 7: 0.026}

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
                # break words that are too long
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


def image_to_bitmap(img, dither=False):
    """Rows of bytes for the printer: bit 1 = black dot (ink),
    most significant bit = leftmost pixel."""
    if img.mode != "L":
        img = img.convert("L")
    if dither:
        bw = img.convert("1", dither=Image.Dither.FLOYDSTEINBERG)
        bw = ImageOps.invert(bw)
    else:
        bw = img.point(lambda p: 255 if p < 128 else 0).convert(
            "1", dither=Image.Dither.NONE)
    return bw.tobytes()


def load_zx_font():
    with open(ZX_FONT_FILE, "rb") as fh:
        return fh.read()


def render_zx_text(text, width, cols=32, margin=0, align="left"):
    """Render text with the ZX Spectrum ROM font.
    `cols` = characters per line (the ZX screen is 32x24), then scale to `width`."""
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
    """Bring the image to ZX resolution (256x192) and scale it to the printhead width."""
    img = Image.open(path).convert("L").resize((256, 192), Image.NEAREST)
    return img.resize((width, max(1, round(192 * width / 256))), Image.NEAREST)


def build_test_image(width):
    """Test page: black band, gradient, text and a final bar."""
    height = 280
    img = Image.new("L", (width, height), 255)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 8, width - 1, 68], fill=0)
    for x in range(width):
        d.line([x, 84, x, 140], fill=int(255 * x / width))
    font = load_font("regular", 30)
    d.text((8, 150), "CATPRINT X6h", font=font, fill=0)
    d.text((8, 190), "print head test ok", font=font, fill=0)
    d.text((8, 230), "abc ABC 123 aeiou", font=font, fill=0)
    d.rectangle([0, height - 18, width - 1, height - 1], fill=0)
    return img


# --- BLE driver -----------------------------------------------------------

class Printer:
    def __init__(self, client, verbose=False):
        self.client = client
        self.verbose = verbose
        self._paused = False
        self.state = None

    def _on_notify(self, _char, data):
        payload = bytes(data)
        if payload == FLOW_PAUSE:
            self._paused = True
        elif payload == FLOW_RESUME:
            self._paused = False
        elif (len(payload) >= 8 and payload[0:3] == MAGIC + bytes([CMD_STATE])
                and payload[3] == 1):
            self.state = payload[6:-2]
        elif self.verbose and payload:
            print("  notify: %s" % payload.hex(), file=sys.stderr)

    async def start(self):
        await self.client.start_notify(RX_UUID, self._on_notify)

    async def _write(self, data):
        while self._paused:
            await asyncio.sleep(0.02)
        await self.client.write_gatt_char(TX_UUID, data, response=False)

    # --- commands ---
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

    async def set_dpi(self):
        await self._write(command(CMD_DPI, b"\x32"))

    async def set_speed(self, value):
        await self._write(command(CMD_SPEED, bytes([value & 0xFF])))

    async def set_energy(self, amount):
        await self._write(command(CMD_ENERGY, amount.to_bytes(2, "little")))

    async def apply_energy(self):
        await self._write(command(CMD_APPLY_ENERGY, b"\x01"))

    async def start_lattice(self):
        await self._write(command(CMD_LATTICE, START_LATTICE))

    async def end_lattice(self):
        await self._write(command(CMD_LATTICE, END_LATTICE))

    async def feed_paper(self, pixels):
        await self._write(command(CMD_FEED, int(pixels).to_bytes(2, "little")))

    async def draw_bitmap(self, row):
        await self._write(command(CMD_BITMAP, bytes(map(reverse_bits, row))))

    # --- print sequence (matches the working X6 implementation) ---
    async def prepare(self, speed, energy):
        await self.get_device_state()
        await self.set_dpi()
        await self.set_energy(energy)
        await self.set_speed(speed)
        await self.apply_energy()
        await self.start_lattice()
        await asyncio.sleep(0.03)

    async def finish(self, feed_rows, row_delay):
        await asyncio.sleep(0.3)
        await self.end_lattice()
        await asyncio.sleep(0.1)
        row_bytes = PAPER_WIDTH // 8
        for _ in range(max(0, feed_rows)):
            await self.draw_bitmap(b"\x00" * row_bytes)
            await asyncio.sleep(row_delay)
        await self.get_device_state()

    async def print_bitmap(self, bitmap, feed, energy, speed, row_delay, pad_bottom=0):
        row_bytes = PAPER_WIDTH // 8
        await self.prepare(speed, energy)
        for i in range(0, len(bitmap), row_bytes):
            row = bitmap[i:i + row_bytes]
            if len(row) < row_bytes:
                row = row + b"\x00" * (row_bytes - len(row))
            await self.draw_bitmap(row)
            await asyncio.sleep(row_delay)
        for _ in range(max(0, pad_bottom)):
            await self.draw_bitmap(b"\x00" * row_bytes)
            await asyncio.sleep(row_delay)
        await self.finish(feed, row_delay)


# --- scanning / connection ------------------------------------------------

async def find_device(name):
    print("Scanning Bluetooth...", file=sys.stderr)
    device = await BleakScanner.find_device_by_name(name, timeout=15)
    if device is not None:
        return device
    # fallback: first device whose name looks like a printer
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
    """Extract printable ASCII runs (>=3 chars) from a raw reply."""
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
    """Connect to the printer and read its status (same BLE link the app uses)."""
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
                payload = bytes(report)[6:-2]
                if not payload:
                    continue
                print("  %-8s    payload: %s" % ("", payload.hex(" ")))
                if cmd == CMD_STATE and len(payload) >= 3:
                    paper = "OUT" if payload[1] & 0x10 else "ok"
                    print("  %-8s    counter=%d  flags=0x%02X  paper=%s"
                          % ("", payload[0], payload[1], paper))
                    volts = payload[2]
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


async def run(args):
    if args.info:
        await show_info(args)
        return
    text = ""
    if args.file:
        text = open(args.file, "r", encoding="utf-8").read()
    elif args.text:
        text = " ".join(args.text)
    elif not sys.stdin.isatty():
        text = sys.stdin.read()

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
    bitmap = image_to_bitmap(img, dither)

    if args.dry_run:
        out = args.dry_run if args.dry_run.endswith(".pbm") else args.dry_run + ".pbm"
        with open(out, "wb") as fh:
            fh.write(b"P4\n%d %d\n" % (img.width, img.height) + bitmap)
        print("Preview saved to %s (%dx%d)" % (out, img.width, img.height))
        return

    if args.energy is not None:
        energy = int(args.energy * 0xFFFF)
    else:
        energy = STRENGTH_ENERGY[args.strength]
    row_delay = args.row_delay
    speed = args.speed

    device_name = args.device
    client = None
    last_error = None
    for attempt in range(1, args.retries + 1):
        target = args.address or await find_device(device_name)
        if target is None:
            print("Attempt %d: printer not found" % attempt, file=sys.stderr)
        else:
            try:
                client = BleakClient(target, timeout=30)
                await client.connect()
                break
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                print("Attempt %d: connection failed (%s)" % (attempt, exc),
                      file=sys.stderr)
                client = None
        if attempt < args.retries:
            await asyncio.sleep(2)
    if client is None:
        raise SystemExit("Cannot connect to '%s'%s" % (
            device_name, ": %s" % last_error if last_error else ""))

    try:
        printer = Printer(client, verbose=args.verbose)
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

        await printer.print_bitmap(bitmap, args.feed, energy, speed, row_delay,
                                   args.pad_bottom)
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
        description="Print text/images on the X6h (Tiny Print) thermal printer over BLE.",
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
    p.add_argument("--strength", type=int, default=7, choices=range(1, 8),
                   help="print strength 1-7 (7 = darkest)")
    p.add_argument("--energy", type=float, default=None,
                   help="thermal energy 0.0-1.0 (overrides --strength)")
    p.add_argument("--speed", type=int, default=1, help="motor speed (lower = faster)")
    p.add_argument("--row-delay", type=float, default=0.035,
                   help="pause between rows in seconds (data pacing)")
    p.add_argument("--feed", type=int, default=80,
                   help="final blank rows to advance the paper (~8 rows = 1 mm)")
    p.add_argument("--pad-bottom", type=int, default=24,
                   help="trailing blank rows to compensate for dropped rows")
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
