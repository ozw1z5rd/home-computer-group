# X6 TinyPrint

![X6 TinyPrint](images/IMG_4314.jpg)

Print text and images on the **X6h "cat printer"** thermal printer (the *Tiny Print*
mobile app) over **Bluetooth Low Energy**, from macOS.

Made by **Home Computer Group** — part of the HCG21 labs.

*English | [Italiano](#italiano)*

---

# English

## Versions

This repo ships **two** drivers for the same printer, sharing the same BLE
transport, rendering and state decoding:

- **v1** — `print.py` / `catprint.sh`: the original, self-contained driver.
- **v2** — `print2.py` / `catprint2.sh`: the same output features, but its
  print pipeline is **derived from the TiMini-Print project**
  (https://github.com/Dejniel/TiMini-Print, Apache-2.0) and follows TiMini's
  `tiny` command dialect for the X6h.

Everything below describes **v1**; the v2 differences and options are in
[Version 2 — TiMini-Print based](#version-2--timini-print-based).

## Why it's not "simple"

The X6h **does not speak ESC/POS**: it is a **raster** printer using a
proprietary "Qx" protocol (`51 78 cmd dir len payload crc8 FF`). It receives a
1-bit bitmap one scanline at a time. On top of that:

- The **motor pace is unstable** (small buffer, no flow control): data must be
  sent at the **right rate**, otherwise scanlines get dropped or compressed.
  Hence the `--speed` (motor speed) and `--row-delay` (pause between rows)
  options.
- The vertical scale is 1:1 (`--vscale 1.0`); if a print comes out
  squashed/stretched, tune `--vscale`.

The Bluetooth serial port `/dev/cu.X6h-xxxx` is **not** used for printing
(BLE only).

## Requirements

- Python 3
- a X6h printer, powered on and in range
- **macOS** (only for the built-in system fonts — `--font regular`/`bold`/… ).
  On other platforms, use the platform-independent `--font zx` or `--font c64`
  bitmap fonts.

## Install

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

## Usage

```bash
# text
./catprint.sh "Hello world!"
./catprint.sh "Receipt no.1\nTotal: 12.50 EUR\nThanks!" --align center --font bold

# from stdin
echo "line 1
line 2" | ./catprint.sh

# image (jpg/png), dithered by default
./catprint.sh --image photo.jpg

# ZX Spectrum screen (256x192, 1:1 pixels, inverted)
./catprint.sh --image screen.png --zx-screen
# same but with screen polarity (background as ink)
./catprint.sh --image screen.png --zx-screen --no-invert

# BASIC listing with the ZX Spectrum ROM font (32 columns)
./catprint.sh -f program.bas --font zx --zx-cols 32
# "true Spectrum" variant (white on black)
./catprint.sh -f program.bas --font zx --zx-cols 32 --invert

# BASIC listing with the Commodore 64 ROM font (40 columns)
./catprint.sh -f program.bas --font c64 --zx-cols 40

# self-test page (black bands + gradient + text)
./catprint.sh --test

# preview without printing (writes a PBM)
./catprint.sh "test" --dry-run /tmp/preview.pbm

# list BLE devices
./catprint.sh --list
```

### Options

| Option | Default | Description |
|---|---|---|
| `--font` | regular | `regular`, `bold`, `mono`, `mono-bold`, `menlo`, `verdana`, `georgia`, `zx`, `c64` |
| `--font-size` | 32 | points (unused by `zx`/`c64`) |
| `--zx-cols` | 32 | characters per line with the ZX/C64 bitmap fonts (ZX screen = 32, C64 screen = 40, max 48) |
| `--invert` / `--no-invert` | auto | invert colors. In `--zx-screen` it is **on** by default; `--no-invert` turns it off |
| `--align` | left | `left`, `center`, `right` |
| `--strength` | 7 | darkness 1-7 (7 = darkest) |
| `--energy` | – | thermal energy 0.0-1.0 (overrides `--strength`) |
| `--speed` | 1 | motor speed (lower = faster) |
| `--row-delay` | 0.035 | pause between rows, seconds (data pacing) |
| `--vscale` | 1.0 | vertical scale compensation (1:1) |
| `--pad-bottom` | 24 | trailing blank rows (prevents text being cut off) |
| `--feed` | 80 | final paper advance in blank rows (~8 rows = 1 mm) |
| `--width` | 384 | printhead width in pixels |
| `--device` | X6h-0000 | Bluetooth name |
| `--address` | – | device UUID (skips scanning) |
| `--retries` | 4 | connection attempts |
| `--delay` | 0.0 | seconds to wait before disconnecting the printer |
| `--info` | – | connect, print firmware/battery/paper status, then exit |
| `--no-dither` | – | disable dithering (on by default for images) |
| `--zx-screen` | off | treat the image as a ZX 256x192 screen (inverted, 1:1) |
| `--verbose` | off | show printer notifications |
| `--dry-run FILE.pbm` | – | only generate a preview |
| `--test` | – | self-test page |

## Fine tuning

- Text **cut off at the bottom** → increase `--pad-bottom`.
- Image **squashed/stretched** vertically → adjust `--vscale`.
- Image **compressed with missing rows** → data is too fast: increase
  `--row-delay` (or increase `--speed`).
- Image **stretched with white gaps** → data is too slow: decrease
  `--row-delay` (or decrease `--speed`).
- Print **too light** → increase `--strength`; **too dark** → decrease it.

## Notes

- The printer is found by Bluetooth name (`X6h-0000` by default).
- On first run macOS may ask for **Bluetooth** permission for the terminal.
- It's a raster printer: text is drawn as an image, so accents and Unicode work
  through the system fonts.
- System fonts (`--font regular`/`bold`/… ) are bundled with **macOS only**.
  On other platforms, text printing refuses with an error unless you use the
  platform-independent `--font zx` or `--font c64` bitmap fonts.
- `--font zx` uses the ZX Spectrum ROM font; `--font c64` uses the Commodore 64
  ROM font (uppercase/graphics set — lowercase renders as uppercase, as on the
  real machine). Both are stored as `zx82.ch8`/`c64.ch8`, 8x8 bitmap fonts.
- `--zx-screen` maps a ZX screen 1:1; with the 384-dot head, 32 columns are
  1.5x, 24 columns are exactly 2x, 48 columns are 1:1.
- Before printing, the printer state is queried: if it reports **no paper**
  (status bit `0x10`) the job aborts instead of printing into the void.
- `--info` reads the `0xA3` state: `battery` is the cell voltage in tenths of a
  volt (e.g. `3.7 V`), `paper` comes from status bit `0x10`.

## Version 2 — TiMini-Print based

`print2.py` (launcher `catprint2.sh`) reuses the protocol code of the
**TiMini-Print** project (https://github.com/Dejniel/TiMini-Print, Apache-2.0)
and follows its `tiny` command dialect for the X6h. BLE transport, rendering and
the `0xA3` state decoding are the same as v1.

### Differences vs `print.py` (v1)

| Aspect | v1 (`print.py`) | v2 (`print2.py`) |
|---|---|---|
| `0xA4` | "DPI", fixed `0x32` | **blackening** `0x30 + level` (1-5) |
| `0xBE` | "apply energy", always `0x01` | **print mode** `1`=text / `0`=image |
| Scanlines | raw `0xA2` only (bit-reversed) | **RLE `0xBF`** when shorter, else `0xA2` |
| `0xBD` | speed setup only | setup + **feed every 200 rows** |
| `0xA6` | **start/end lattice** (`AA 55 …`) | not used |
| End of page | blank `0xA2` rows (`--feed`, `--pad-bottom`) | `0xBD` + `0xA1`x2 + `0xBD` + `0xA3` |
| Energy | `--strength 1-7` (8000…30000) | `--profile {d1,x6h}` + `--energy` |
| Paper motion | – | `--feed` / `--retract` (`0xA1`/`0xA0`) |

Identical in both: packet framing (`51 78 cmd 00 len crc8 FF`), BLE
characteristics (`ae30`/`ae01`/`ae02`), rendering (PIL, system fonts, ZX and
C64 fonts, dithering, `--zx-screen`, `--dry-run`, `--test`) and the **`0xA3`
state-payload decoding** (paper-out bit `0x10`, battery voltage).

### Usage

```bash
./catprint2.sh "Hello world"
./catprint2.sh --image photo.jpg --energy 9500
./catprint2.sh -f program.bas --font zx --zx-cols 40 --energy 15000
./catprint2.sh -f program.bas --font c64 --zx-cols 40 --energy 15000
./catprint2.sh --feed          # advance paper one step
./catprint2.sh --retract       # retract paper one step
```

### v2 options

| Option | Default | Description |
|---|---|---|
| `--profile` | d1 | TiMini profile for the X6h: `d1` (image 5000 / text 8000) or `x6h` (9500/9500) |
| `--energy` | – | raw thermal energy, overrides the profile |
| `--blackening` | 3 | dot blackening 1-5 (`0xA4`) |
| `--speed` | 1 | motor speed (`0xBD`) |
| `--dpi` | 200 | paper DPI for `0xA1`/`0xA0` (`30 00` = 200, `48 00` = 300) |
| `--feed-padding` | 12 | final feed value (`0xBD`) |
| `--post-feed` | 2 | number of `0xA1` paper packets at the end of a page |
| `--row-delay` | 0.035 | pause between scanlines, seconds (pacing) |
| `--feed` / `--retract` | – | send a single paper-motion packet and exit |

### Pacing

The X6h does **not** emit `0xAE` flow-control notifications (verified on all
notify characteristics), so TiMini-Print's chunk streaming cannot
self-regulate and the output comes out in bursts. `print2.py` therefore paces
**one scanline per BLE write** with a constant `--row-delay`, matching v1.

## Acknowledgements

- The v2 protocol code (`print2.py`) is **based on TiMini-Print** by
  **Dejniel** (https://github.com/Dejniel/TiMini-Print, Apache-2.0).
- Protocol format documented by **parzivail**, *"Documenting the X6h Mini BLE
  Thermal Printer"*.
- Inspired by the community projects **Cat-Printer** (NaitLee) and
  **TinyPOS-Bridge** (sajjad-amin).
- ZX Spectrum ROM font (`zx82.ch8`) from **ivop/8x8-fonts**.
- Commodore 64 ROM font (`c64.ch8`) from the C64 character ROM (uppercase/graphics set).
- Thanks to the **bleak** and **Pillow** maintainers.
- Sample ZX screens and listings belong to their respective authors and are
  included for testing only.

## License

Released under the **GNU General Public License v3.0 or later**
(SPDX: `GPL-3.0-or-later`). See [LICENSE](LICENSE).

---

# Italiano

Stampa testo e immagini sulla stampante termica **X6h** (le piccole "cat
printer" dell'app *Tiny Print*) via **Bluetooth Low Energy**, dal Mac.

Realizzato da **Home Computer Group** — parte dei laboratori HCG21.

## Versioni

Questo repo contiene **due** driver per la stessa stampante, che condividono
trasporto BLE, renderizzazione e decodifica di stato:

- **v1** — `print.py` / `catprint.sh`: il driver originale, autonomo.
- **v2** — `print2.py` / `catprint2.sh`: le stesse funzioni di stampa, ma la
  pipeline è **derivata dal progetto TiMini-Print**
  (https://github.com/Dejniel/TiMini-Print, Apache-2.0) e segue il dialetto di
  comandi `tiny` di TiMini per la X6h.

Tutto quello che segue descrive la **v1**; differenze e opzioni della v2 sono in
[Versione 2 — basata su TiMini-Print](#versione-2--basata-su-timini-print).

## Perché non è "semplice"

La X6h **non parla ESC/POS**: è una stampante **raster** con protocollo
proprietario "Qx" (`51 78 cmd dir len payload crc8 FF`). Riceve una bitmap
monocromatica riga per riga. Inoltre:

- La **velocità del motore è instabile** (buffer piccolo, niente controllo di
  flusso): i dati vanno inviati al **ritmo giusto**, altrimenti righe vengono
  scartate o compresse. Da qui i parametri `--speed` e `--row-delay`.
- La scala verticale è 1:1 (`--vscale 1.0`); se una stampa esce
  schiacciata/allungata si regola `--vscale`.

La porta seriale Bluetooth `/dev/cu.X6h-xxxx` **non** serve per stampare (solo
BLE).

## Requisiti

- Python 3
- una stampante X6h, accesa e nel raggio
- **macOS** (solo per i font di sistema integrati — `--font regular`/`bold`/… ).
  Su altre piattaforme, usa i font bitmap indipendenti dalla piattaforma
  `--font zx` o `--font c64`.

## Installazione

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

## Uso

```bash
# testo
./catprint.sh "Ciao mondo!"
./catprint.sh "Scontrino n.1\nTotale: 12,50 EUR\nGrazie!" --align center --font bold

# da stdin
echo "riga 1
riga 2" | ./catprint.sh

# immagine (jpg/png), con dithering (default)
./catprint.sh --image foto.jpg

# schermata ZX Spectrum (256x192, pixel 1:1, invertita)
./catprint.sh --image schermata.png --zx-screen
# come sopra ma con la polarita' dello schermo (fondo in inchiostro)
./catprint.sh --image schermata.png --zx-screen --no-invert

# listato in BASIC con il font ROM dello ZX Spectrum (32 colonne)
./catprint.sh -f programma.bas --font zx --zx-cols 32
# variante "vera" dello Spectrum (bianco su nero)
./catprint.sh -f programma.bas --font zx --zx-cols 32 --invert

# listato in BASIC con il font ROM del Commodore 64 (40 colonne)
./catprint.sh -f programma.bas --font c64 --zx-cols 40

# pagina di collaudo (bande nere + gradiente + testo)
./catprint.sh --test

# anteprima senza stampare (genera un PBM)
./catprint.sh "test" --dry-run /tmp/anteprima.pbm

# elenco dispositivi BLE
./catprint.sh --list
```

### Opzioni

| Opzione | Default | Descrizione |
|---|---|---|
| `--font` | regular | `regular`, `bold`, `mono`, `mono-bold`, `menlo`, `verdana`, `georgia`, `zx`, `c64` |
| `--font-size` | 32 | punti (non usato da `zx`/`c64`) |
| `--zx-cols` | 32 | caratteri per riga coi font bitmap ZX/C64 (schermata ZX = 32, schermata C64 = 40, max 48) |
| `--invert` / `--no-invert` | auto | inverti i colori. In `--zx-screen` è **attivo** di default; `--no-invert` lo disattiva |
| `--align` | left | `left`, `center`, `right` |
| `--strength` | 7 | intensità 1-7 (7 = più scuro) |
| `--energy` | – | energia termica 0.0-1.0 (sovrascrive `--strength`) |
| `--speed` | 1 | velocità motore (più basso = più veloce) |
| `--row-delay` | 0.035 | pausa tra le righe in secondi (ritmo dei dati) |
| `--vscale` | 1.0 | compensazione scala verticale (1:1) |
| `--pad-bottom` | 24 | righe bianche in fondo (evita il taglio del testo) |
| `--feed` | 80 | avanzamento carta finale in righe bianche (~8 righe = 1 mm) |
| `--width` | 384 | larghezza testina in pixel |
| `--device` | X6h-0000 | nome Bluetooth |
| `--address` | – | UUID del dispositivo (salta la scansione) |
| `--retries` | 4 | tentativi di connessione |
| `--delay` | 0.0 | secondi di attesa prima di scollegare la stampante |
| `--info` | – | si collega, mostra firmware/batteria/carta, ed esce |
| `--no-dither` | – | disattiva il dithering (attivo di default per le immagini) |
| `--zx-screen` | off | tratta l'immagine come schermata ZX 256x192 (invertita, 1:1) |
| `--verbose` | off | mostra le notifiche della stampante |
| `--dry-run FILE.pbm` | – | genera solo l'anteprima |
| `--test` | – | pagina di collaudo |

## Regolazione fine

- Testo **tagliato in fondo** → aumenta `--pad-bottom`.
- Immagine **schiacciata/allungata** in altezza → regola `--vscale`.
- Immagine **compressa e righe mancanti** → i dati vanno troppo veloci:
  aumenta `--row-delay` (o aumenta `--speed`).
- Immagine **allungata con spazi bianchi** → i dati vanno troppo lenti:
  diminuisci `--row-delay` (o diminuisci `--speed`).
- Stampa **chiara** → aumenta `--strength`; **troppo scura** → diminuiscila.

## Note

- La stampante si trova per nome Bluetooth (`X6h-0000` di default).
- Alla prima esecuzione macOS può chiedere il permesso **Bluetooth** al terminale.
- È una stampante raster: il testo è disegnato come immagine, quindi accenti e
  Unicode funzionano tramite i font di sistema.
- I font di sistema (`--font regular`/`bold`/… ) sono inclusi **solo in macOS**.
  Su altre piattaforme, la stampa del testo viene rifiutata con un errore a
  meno che si usino i font bitmap indipendenti dalla piattaforma `--font zx` o
  `--font c64`.
- `--font zx` usa il font ROM dello ZX Spectrum; `--font c64` usa il font ROM
  del Commodore 64 (set maiuscole/grafica — le minuscole vengono rese come
  maiuscole, come sulla macchina reale). Entrambi sono salvati come
  `zx82.ch8`/`c64.ch8`, font bitmap 8x8.
- `--zx-screen` mappa la schermata ZX 1:1; con la testina da 384 dot, 32 colonne
  sono 1.5x, 24 colonne sono esattamente 2x, 48 colonne sono 1:1.
- Prima di stampare viene letto lo stato: se la stampante segnala **carta
  finita** (bit `0x10`) il lavoro si interrompe invece di stampare a vuoto.
- `--info` legge lo stato `0xA3`: `battery` è la tensione della cella in decimi
  di volt (es. `3.7 V`), `paper` deriva dal bit di stato `0x10`.

## Versione 2 — basata su TiMini-Print

`print2.py` (launcher `catprint2.sh`) riusa il codice di protocollo del
progetto **TiMini-Print** (https://github.com/Dejniel/TiMini-Print, Apache-2.0)
e segue il suo dialetto di comandi `tiny` per la X6h. Trasporto BLE,
renderizzazione e decodifica dello stato `0xA3` sono identici alla v1.

### Differenze rispetto a `print.py` (v1)

| Aspetto | v1 (`print.py`) | v2 (`print2.py`) |
|---|---|---|
| `0xA4` | "DPI", payload fisso `0x32` | **blackening** `0x30 + livello` (1-5) |
| `0xBE` | "apply energy", sempre `0x01` | **print mode** `1`=testo / `0`=immagine |
| Righe | solo raw `0xA2` (bit invertiti) | **RLE `0xBF`** se più corto, altrimenti `0xA2` |
| `0xBD` | solo setup velocità | setup + **feed ogni 200 righe** |
| `0xA6` | **start/end lattice** (`AA 55 …`) | non usato |
| Fine pagina | righe bianche `0xA2` (`--feed`, `--pad-bottom`) | `0xBD` + `0xA1`x2 + `0xBD` + `0xA3` |
| Energia | `--strength 1-7` (8000…30000) | `--profile {d1,x6h}` + `--energy` |
| Movimento carta | – | `--feed` / `--retract` (`0xA1`/`0xA0`) |

Identici in entrambe: framing dei pacchetti (`51 78 cmd 00 len crc8 FF`),
characteristic BLE (`ae30`/`ae01`/`ae02`), renderizzazione (PIL, font di
sistema, font ZX e C64, dithering, `--zx-screen`, `--dry-run`, `--test`) e la
**decodifica del payload di stato `0xA3`** (bit carta finita `0x10`, tensione
batteria).

### Uso

```bash
./catprint2.sh "Ciao mondo"
./catprint2.sh --image foto.jpg --energy 9500
./catprint2.sh -f programma.bas --font zx --zx-cols 40 --energy 15000
./catprint2.sh -f programma.bas --font c64 --zx-cols 40 --energy 15000
./catprint2.sh --feed          # avanzamento carta di un passo
./catprint2.sh --retract       # riavvolgimento carta di un passo
```

### Opzioni v2

| Opzione | Default | Descrizione |
|---|---|---|
| `--profile` | d1 | profilo TiMini per la X6h: `d1` (immagine 5000 / testo 8000) o `x6h` (9500/9500) |
| `--energy` | – | energia termica grezza, sovrascrive il profilo |
| `--blackening` | 3 | blackening 1-5 (`0xA4`) |
| `--speed` | 1 | velocità motore (`0xBD`) |
| `--dpi` | 200 | DPI carta per `0xA1`/`0xA0` (`30 00` = 200, `48 00` = 300) |
| `--feed-padding` | 12 | valore di feed finale (`0xBD`) |
| `--post-feed` | 2 | numero di pacchetti carta `0xA1` a fine pagina |
| `--row-delay` | 0.035 | pausa tra le righe in secondi (pacing) |
| `--feed` / `--retract` | – | invia un singolo pacchetto di movimento carta ed esce |

### Pacing

La X6h **non** emette notifiche di flow-control `0xAE` (verificato su tutte le
characteristic notify), quindi lo streaming a blocchi di TiMini-Print non può
autoregolarsi e l'uscita risulta "a scatti". `print2.py` invia quindi **una
scanline per scrittura BLE** con `--row-delay` costante, come la v1.

## Riconoscimenti

- Il codice di protocollo della v2 (`print2.py`) è **basato su TiMini-Print** di
  **Dejniel** (https://github.com/Dejniel/TiMini-Print, Apache-2.0).
- Formato del protocollo documentato da **parzivail**, *"Documenting the X6h Mini
  BLE Thermal Printer"*.
- Ispirato ai progetti della community **Cat-Printer** (NaitLee) e
  **TinyPOS-Bridge** (sajjad-amin).
- Font ROM dello ZX Spectrum (`zx82.ch8`) da **ivop/8x8-fonts**.
- Font ROM del Commodore 64 (`c64.ch8`) dal character ROM C64 (set maiuscole/grafica).
- Grazie ai manutentori di **bleak** e **Pillow**.
- Le schermate e i listati ZX di esempio appartengono ai rispettivi autori e
  sono inclusi solo a scopo di test.

## Licenza

Rilasciato sotto **GNU General Public License v3.0 o successiva**
(SPDX: `GPL-3.0-or-later`). Vedi [LICENSE](LICENSE).
