#!/usr/bin/env python3
"""Export Samsung Notes from a Smart Switch PC backup (macOS or Windows).

Decrypts SAMSUNGNOTE/SamsungNote.SNMM, extracts every note as .sdocx
(grouped by folder), and converts them to PDF if `sdocx-cli` is on PATH.

Usage:
    python3 samsung_notes_export.py [backup_dir] [out_dir]

Without backup_dir, looks for backups in the default Smart Switch folders.
out_dir defaults to notes-export/ next to this script.

Needs: pycryptodome or cryptography (pip install pycryptodome).
Optional: sdocx-cli for PDFs
    cargo install --git https://github.com/twangodev/sdocx sdocx-cli
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from pathlib import Path

FIXED_KEY = b"0b1e96db05d64ea4"  # Smart Switch PC key for <Dummy>
BACKUP_ROOTS = (
    Path.home() / "Samsung" / "SmartSwitch" / "Backup",
    Path.home() / "Documents" / "Samsung" / "SmartSwitch" / "Backup",
)
DEFAULT_OUT = Path(__file__).resolve().parent / "notes-export"


def aes_cbc(key, iv):
    """Return a stateful CBC decrypt function (no unpadding)."""
    try:
        from Crypto.Cipher import AES
        c = AES.new(key, AES.MODE_CBC, iv)
        return c.decrypt
    except ImportError:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        d = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
        return d.update


def is_hex(b):
    try:
        s = b.decode("ascii")
    except UnicodeDecodeError:
        return None
    return s if 32 <= len(s) <= 128 and re.fullmatch(r"[0-9a-fA-F]+", s) else None


def session_dummy(backup):
    xml = ET.parse(backup / "backupHistoryInfo.xml")
    ct = None
    for el in xml.iter():
        if el.tag.rsplit("}", 1)[-1] == "Dummy" and (el.text or "").strip():
            ct = bytes.fromhex(el.text.strip())
            break
    if ct is None:
        sys.exit("No <Dummy> in backupHistoryInfo.xml")
    # macOS: AES-128-CBC, zero IV, PKCS#7
    p = aes_cbc(FIXED_KEY, b"\0" * 16)(ct)
    n = p[-1]
    if 1 <= n <= 16 and p.endswith(bytes([n]) * n):
        s = is_hex(p[:-n])
        if s:
            return s
    # Windows: AES-128-ECB, zero padding (ECB == CBC with zero IV per block,
    # so redo it block by block)
    out = b"".join(aes_cbc(FIXED_KEY, b"\0" * 16)(ct[i:i + 16]) for i in range(0, len(ct), 16))
    s = is_hex(out.rstrip(b"\0"))
    if s:
        return s
    sys.exit("Could not decrypt the session Dummy (password-protected backup?)")


def decrypt_sdoc(snmm, key, dest):
    """Stream-decrypt sdoc.bk (16-byte IV + AES-CBC + PKCS#7) to dest."""
    with zipfile.ZipFile(snmm) as z, z.open("sdoc.bk") as src, open(dest, "wb") as out:
        iv = src.read(16)
        dec = aes_cbc(key, iv)
        tail = b""
        total = z.getinfo("sdoc.bk").file_size
        done = 16
        while True:
            chunk = src.read(4 * 1024 * 1024)
            if not chunk:
                break
            done += len(chunk)
            buf = tail + chunk
            cut = (len(buf) // 16) * 16 - 16  # keep last block for unpadding
            if cut > 0:
                out.write(dec(buf[:cut]))
                tail = buf[cut:]
            else:
                tail = buf
            print(f"\r  decrypting {done * 100 // total}%", end="", flush=True)
        last = dec(tail)
        n = last[-1]
        if 1 <= n <= 16 and last.endswith(bytes([n]) * n):
            last = last[:-n]
        out.write(last)
    print()


def safe(name):
    return re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", name).strip() or "_"


def find_backups():
    """Return backups in the default folders, newest first."""
    found = [p.parent for root in BACKUP_ROOTS if root.is_dir()
             for p in root.glob("*/backupHistoryInfo.xml")]
    return sorted(found, key=lambda p: p.stat().st_mtime, reverse=True)


def choose_backup():
    found = find_backups()
    if not found:
        roots = "\n".join(f"  {r}" for r in BACKUP_ROOTS)
        sys.exit(f"No Smart Switch backup found in:\n{roots}\n"
                 "Run a backup first, or pass the backup folder as an argument.")
    if len(found) == 1:
        return found[0]
    if not sys.stdin.isatty():
        sys.exit("Several backups found; pass the one you want as an argument.")
    print("Several backups found (newest first):")
    for i, p in enumerate(found, 1):
        print(f"  {i}. {p.name}")
    choice = input(f"Which one? [1-{len(found)}, default 1] ").strip() or "1"
    if not choice.isdigit() or not 1 <= int(choice) <= len(found):
        sys.exit(f"Invalid choice: {choice}")
    return found[int(choice) - 1]


def find_sdocx_cli():
    cargo_bin = Path.home() / ".cargo" / "bin" / "sdocx-cli"
    return shutil.which("sdocx-cli") or shutil.which(str(cargo_bin))


def main():
    if len(sys.argv) > 3 or {"-h", "--help"} & set(sys.argv):
        sys.exit(__doc__)
    backup = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else choose_backup()
    out = Path(sys.argv[2]).expanduser() if len(sys.argv) > 2 else DEFAULT_OUT
    snmm = backup / "SAMSUNGNOTE" / "SamsungNote.SNMM"
    if not snmm.is_file():
        sys.exit(f"Not found: {snmm}\n"
                 "This folder is not a backup, or the backup has no Samsung Notes in it.")

    print(f"Using backup: {backup}")
    dummy = session_dummy(backup)
    key = hashlib.sha256(dummy.encode()).digest()[:16]
    print("Session key recovered.")

    work = out / "_work"
    work.mkdir(parents=True, exist_ok=True)
    sdoc_zip = work / "sdoc.zip"
    decrypt_sdoc(snmm, key, sdoc_zip)

    with zipfile.ZipFile(sdoc_zip) as z:
        names = set(z.namelist())
        notes = json.loads(z.read("sdoc.list"))["file_info"]
        cats = {}
        if "category.list" in names:
            for c in json.loads(z.read("category.list")).get("category_info", []):
                cats[c["category_uuid"]] = c.get("name") or "Folder"

        sdocx_dir = out / "sdocx"
        written = []
        for n in notes:
            fn = n["filename"]
            entry = next((e for e in (fn, "b_" + fn) if e in names), None)
            if entry is None:
                print(f"  missing in backup: {fn}")
                continue
            folder = safe(cats.get(n.get("category_uuid"), "Uncategorized"))
            if n.get("deleted"):
                folder = "_Trash"
            ts = n.get("createTime") or n.get("timestamp") or 0
            stamp = datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d_%H%M")
            dst = sdocx_dir / folder / f"{stamp}_{Path(fn).stem}.sdocx"
            dst.parent.mkdir(parents=True, exist_ok=True)
            with z.open(entry) as s, open(dst, "wb") as d:
                shutil.copyfileobj(s, d)
            written.append(dst)
    # Decrypted copy of every note, no longer needed once extracted.
    shutil.rmtree(work)
    print(f"Extracted {len(written)} of {len(notes)} notes to {sdocx_dir}")

    cli = find_sdocx_cli()
    if not cli:
        print("sdocx-cli not found; skipping PDF. Install with:\n"
              "  cargo install --git https://github.com/twangodev/sdocx sdocx-cli")
        return
    pdf_dir = out / "pdf"
    failed = []
    for i, src in enumerate(written, 1):
        dst = pdf_dir / src.relative_to(sdocx_dir).with_suffix(".pdf")
        dst.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run([cli, str(src), "-o", str(dst)], capture_output=True, text=True)
        print(f"\r  PDF {i}/{len(written)}", end="", flush=True)
        if r.returncode != 0 or not dst.exists():
            failed.append((src, (r.stderr or r.stdout).strip().splitlines()[-1:]))
    print()
    print(f"PDFs in {pdf_dir} ({len(written) - len(failed)} ok, {len(failed)} failed)")
    for src, err in failed:
        print(f"  FAILED {src.name}: {err}")


if __name__ == "__main__":
    main()
