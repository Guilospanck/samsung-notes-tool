#!/usr/bin/env bash
# One-step export: sets up Python, offers to install sdocx-cli, runs the tool.
# Usage: ./run.sh [backup_dir] [out_dir]
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SDOCX_REPO="https://github.com/twangodev/sdocx"

if ! command -v python3 >/dev/null; then
    echo "python3 not found. Install it from https://www.python.org/downloads/ and retry." >&2
    exit 1
fi

if [ ! -x "$DIR/.venv/bin/python" ]; then
    echo "Setting up Python environment..."
    python3 -m venv "$DIR/.venv"
fi
if ! "$DIR/.venv/bin/python" -c "import Crypto" 2>/dev/null; then
    "$DIR/.venv/bin/python" -m pip install --quiet -r "$DIR/requirements.txt"
fi

export PATH="$HOME/.cargo/bin:$PATH"
if ! command -v sdocx-cli >/dev/null; then
    if ! command -v cargo >/dev/null; then
        echo "sdocx-cli needs Rust to install, and Rust is not installed."
        echo "Without it you get .sdocx files but no PDFs."
        echo "To get PDFs: install Rust from https://rustup.rs, then run this script again."
    elif [ -t 0 ]; then
        read -r -p "Install sdocx-cli for PDF output? It takes a few minutes. [Y/n] " answer
        case "$answer" in
            [nN]*) ;;
            *) cargo install --git "$SDOCX_REPO" sdocx-cli ;;
        esac
    fi
fi

exec "$DIR/.venv/bin/python" "$DIR/samsung_notes_export.py" "$@"
