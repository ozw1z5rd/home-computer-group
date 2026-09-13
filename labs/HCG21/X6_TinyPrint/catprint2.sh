#!/bin/sh
# X6 TinyPrint - wrapper that runs print2.py with the project virtualenv.
# Copyright (C) 2026 Home Computer Group
# SPDX-License-Identifier: GPL-3.0-or-later
DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$DIR/.venv/bin/python" "$DIR/print2.py" "$@"
