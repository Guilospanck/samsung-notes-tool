# Pass paths with spaces through to the script intact.
set positional-arguments

python := ".venv/bin/python"
sdocx_repo := "https://github.com/twangodev/sdocx"

# List the recipes.
default:
    @just --list

# Create the Python environment and install its dependencies.
setup:
    #!/usr/bin/env bash
    set -euo pipefail
    if ! command -v python3 >/dev/null; then
        echo "python3 not found. Install it from https://www.python.org/downloads/ and retry." >&2
        exit 1
    fi
    if [ ! -x "{{python}}" ]; then
        echo "Setting up Python environment..."
        python3 -m venv .venv
    fi
    if ! "{{python}}" -c "import Crypto" 2>/dev/null; then
        "{{python}}" -m pip install --quiet -r requirements.txt
    fi

# Install sdocx-cli, which makes the PDFs. Needs Rust.
install-cli:
    #!/usr/bin/env bash
    set -euo pipefail
    export PATH="$HOME/.cargo/bin:$PATH"
    if ! command -v cargo >/dev/null; then
        echo "sdocx-cli needs Rust to install, and Rust is not installed." >&2
        echo "Install Rust from https://rustup.rs, then run this recipe again." >&2
        exit 1
    fi
    cargo install --git "{{sdocx_repo}}" sdocx-cli

# Export notes from a Smart Switch backup: just export [backup_dir] [out_dir]
export *args: setup
    @"{{python}}" samsung_notes_export.py "$@"

# Make PDFs from existing .sdocx files: just convert [sdocx_dir] [pdf_dir]
convert *args: setup
    @"{{python}}" samsung_notes_export.py --convert "$@"

# Make one PDF: just note note.sdocx [-o out.pdf] [--pages 1-3,5]
note file *args:
    @export PATH="$HOME/.cargo/bin:$PATH"; sdocx-cli -f pdf "$@"

# Zip the .sdocx files, the copy worth keeping: just zip-sdocx [out_dir]
zip-sdocx out="notes-export":
    cd "$1" && zip -9 -r -X -FS samsung-notes-sdocx.zip sdocx -x '*.DS_Store'

# Zip the PDFs: just zip-pdf [out_dir]
zip-pdf out="notes-export":
    cd "$1" && zip -9 -r -X -FS samsung-notes-pdfs.zip pdf -x '*.DS_Store'

# Delete the leftover decrypted notes in _work: just clean [out_dir]
clean out="notes-export":
    rm -rf "$1/_work"

# Remove the Python environment and sdocx-cli. Keeps your exported notes.
uninstall:
    #!/usr/bin/env bash
    set -euo pipefail
    export PATH="$HOME/.cargo/bin:$PATH"
    rm -rf .venv __pycache__
    echo "Removed the Python environment."
    if ! command -v cargo >/dev/null; then
        echo "cargo not found; skipping sdocx-cli."
    elif cargo install --list | grep '^sdocx-cli ' >/dev/null; then
        cargo uninstall sdocx-cli
    else
        echo "sdocx-cli is not installed."
    fi
