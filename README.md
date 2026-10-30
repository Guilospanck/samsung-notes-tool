# samsung-notes-tool

Get your Samsung Notes off your Galaxy phone or tablet and onto your computer as PDFs.

Samsung Smart Switch can back up your notes, but the backup is encrypted and can only be restored to a Samsung device. This tool decrypts a backup you made yourself, sorts your notes into your Samsung Notes folders, and converts each one to PDF.

Everything runs on your computer. The tool does not upload your notes anywhere.

Tested on macOS with Smart Switch 5.0.69.1. The code also handles Windows backups, but that path has not been tested end to end.

## Quick start (macOS)

If you already have a backup and the tools installed:

```sh
just export
```

Your PDFs appear in `notes-export/pdf/`. If this is your first time, follow the steps below. If you already have the `.sdocx` files, see [If you already have the .sdocx files](#if-you-already-have-the-sdocx-files).

Run `just` on its own to list every recipe:

| Recipe | What it does |
| --- | --- |
| `just setup` | Creates the Python environment and installs its dependencies. The other recipes run this for you. |
| `just install-cli` | Installs `sdocx-cli`, the program that makes the PDFs. Needs Rust. |
| `just export [backup_dir] [out_dir]` | Decrypts a Smart Switch backup, extracts the `.sdocx` files, and makes PDFs. |
| `just convert [sdocx_dir] [pdf_dir]` | Makes PDFs from `.sdocx` files you already have. No backup needed. |
| `just note <file> [options]` | Makes a PDF from one `.sdocx` file. Options go to `sdocx-cli`, such as `-o out.pdf` or `--pages 1-3,5`. |
| `just zip-sdocx [out_dir]` | Zips the `.sdocx` files into `samsung-notes-sdocx.zip` inside `out_dir`. |
| `just zip-pdf [out_dir]` | Zips the PDFs into `samsung-notes-pdfs.zip` inside `out_dir`. |
| `just clean [out_dir]` | Deletes the `_work` folder, if an interrupted export left one. |
| `just uninstall` | Removes the Python environment and `sdocx-cli`. Keeps your exported notes. |

## Step by step

### 1. Install Smart Switch

1. Download Smart Switch from [Samsung's Smart Switch page](https://www.samsung.com/us/support/answer/ANS00048603/).
2. Install it and open it.
3. On a Mac, remove Android File Transfer if you have it. [Samsung says](https://www.samsung.com/au/apps/smart-switch/faq-smart-switch-pc-or-mac) Smart Switch will not run alongside it.

### 2. Back up your device

1. Connect your device to the computer with a USB cable that carries data. Some cables only charge.
2. Unlock the device and tap **Allow** when it asks for permission.
3. In Smart Switch, click **Backup**.
4. Choose what to back up, and make sure **Samsung Notes** is selected. You can untick everything else to make the backup faster.
5. **Do not set a backup password.** This tool cannot open password-protected backups.
6. Wait until Smart Switch says the backup is finished, then disconnect the device.

**Locked notes:** Smart Switch says locked notes are not backed up. Unlock any note you want to keep before you start the backup.

### 3. Install what the tool needs

You need Python and [just](https://github.com/casey/just), and Rust if you want PDFs.

1. Open the Terminal app.
2. Check for Python by running `python3 --version`. If you get an error, install Python from [python.org](https://www.python.org/downloads/).
3. Install the Xcode Command Line Tools, which Rust needs to build programs on a Mac:

   ```sh
   xcode-select --install
   ```

4. Install Rust from [rustup.rs](https://rustup.rs), then close and reopen Terminal.
5. Install just. With [Homebrew](https://brew.sh), run `brew install just`. For other options, see the [just install guide](https://github.com/casey/just#installation).

### 4. Download this tool

If you have Git:

```sh
git clone <this repository's URL>
cd samsung-notes-tool
```

Otherwise, download the ZIP from this repository's page, unzip it, then type `cd ` in Terminal (with the space), drag the folder onto the Terminal window, and press Return.

### 5. Run it

Install `sdocx-cli`, the program that makes the PDFs. It takes a few minutes, and you only need to do it once:

```sh
just install-cli
```

Then export your notes:

```sh
just export
```

The recipe sets up what it needs, finds your backup, and exports your notes.

If you have several backups, the tool asks which one to use.

### 6. Find your notes

| Folder | What is in it |
| --- | --- |
| `notes-export/pdf/` | One PDF per note, in your Samsung Notes folders |
| `notes-export/sdocx/` | The original note files |

Each file is named with the date the note was created, then the note's internal ID. Notes in the Samsung Notes trash go in a `_Trash` folder.

Keep the `sdocx` folder. It is the original data, and you can use it to retry any note that failed to convert.

## Ways to make a PDF

| Starting from | Command | Use it when |
| --- | --- | --- |
| A Smart Switch backup | `just export [backup_dir] [out_dir]` | First export, or you have new notes on your device. Gives you `.sdocx` files and PDFs. |
| A folder of `.sdocx` files | `just convert [sdocx_dir] [pdf_dir]` | You want to rebuild the PDFs, for example after downloading your notes from cloud storage. |
| One `.sdocx` file | `just note note.sdocx -o note.pdf` | You want one note, or only some pages of it with `--pages 1-3,5`. |

## What to keep

Keep the `.sdocx` files. They are the original notes in their Samsung Notes folders, and you can rebuild the PDFs from them without the backup.

```sh
just zip-sdocx
```

| Item | Keep it? | Why |
| --- | --- | --- |
| `notes-export/sdocx/` | Yes | The original notes. Every PDF can be rebuilt from here. |
| `notes-export/pdf/` | Optional | Lets you read notes without any tools, but a note that failed to convert has no PDF. Zip it with `just zip-pdf`. |
| `notes-export/_work/` | No | A decrypted copy of the same notes. It should only exist if an export stopped early. Remove it with `just clean`. |
| The Smart Switch backup | No | You do not need it once you have the `.sdocx` files, and it holds private data such as your IMEI. |

Expect the zip to be only a little smaller than the folder, because `.sdocx` files and PDFs are already compressed. The zip is not encrypted, so encrypt it before you upload it.

## If you already have the .sdocx files

You do not need the Smart Switch backup to make PDFs again. The `.sdocx` files are enough, so you can keep only those, for example in cloud storage, and convert them when you need to. This step needs `sdocx-cli`, so run `just install-cli` first if it is not installed.

Convert the files in `notes-export/sdocx/`:

```sh
just convert
```

Or choose the folders yourself:

```sh
just convert "/path/to/sdocx" "/path/to/pdf"
```

The tool searches `sdocx_dir` and its subfolders, and keeps the same folders under `pdf_dir`. If you leave out `pdf_dir`, the PDFs go in a `pdf` folder next to `sdocx_dir`. Existing PDFs with the same name are overwritten.

`.sdocx` files are not encrypted. Encrypt them before you upload them, unless you trust the storage provider with every note.

## Other ways to run it

Use a backup in a different folder, or write the export somewhere else:

```sh
just export "/path/to/backup" "/path/to/output"
```

The backup folder is the one that contains `backupHistoryInfo.xml` and `SAMSUNGNOTE/`.

Smart Switch normally saves backups in one of these folders, and the tool checks both:

- `~/Samsung/SmartSwitch/Backup/`
- `~/Documents/Samsung/SmartSwitch/Backup/`

On Windows, the recipes need a Unix-style shell, so run these commands instead:

```bat
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python samsung_notes_export.py
```

To convert existing `.sdocx` files, run `.venv\Scripts\python samsung_notes_export.py --convert [sdocx_dir] [pdf_dir]`.

For PDFs, also install Rust and run the `cargo install` command shown in [Manual setup](#manual-setup).

## Manual setup

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cargo install --git https://github.com/twangodev/sdocx sdocx-cli
.venv/bin/python samsung_notes_export.py [backup_dir] [out_dir]
.venv/bin/python samsung_notes_export.py --convert [sdocx_dir] [pdf_dir]
```

## Uninstall

```sh
just uninstall
```

This removes the `.venv` folder and `sdocx-cli`. It does not touch `notes-export/`, your backups, Rust, Python, or just. Delete those yourself if you no longer want them.

## Troubleshooting

| Message or problem | What to do |
| --- | --- |
| `No Smart Switch backup found` | Finish a backup first. If it is in another folder, pass that folder to `just export`. |
| `No .sdocx files found` | Check the folder you passed to `just convert`. Without one, it looks in `notes-export/sdocx/`. |
| `Not found: .../SamsungNote.SNMM` | The backup has no notes. Run the backup again with Samsung Notes selected. |
| `Could not decrypt the session Dummy` | The backup probably has a password. Make a new backup without one. |
| `sdocx-cli not found; skipping PDF` or `sdocx-cli: command not found` | You still have the `.sdocx` files. Install Rust, run `just install-cli`, then run `just convert`. |
| `command not found: just` | Install just, as described in [step 3](#3-install-what-the-tool-needs). |
| A few notes show `FAILED` | The `sdocx-cli` converter could not read those notes, which can happen with very large or unusual ones. Check for a newer `sdocx-cli`, export that note as a PDF from the Samsung Notes app, or report the error to [that project](https://github.com/twangodev/sdocx/issues). Do not attach a private note. |
| The device is not detected | Try another USB cable or port, and check that the device is unlocked. |

## Privacy

- Your exported notes are unencrypted. Store them somewhere safe.
- A backup folder holds private data, including your device's IMEI (its unique hardware ID). Do not share it, or attach it to a bug report.
- `.gitignore` excludes exports and backup files so they are not committed by accident. Keep them out of this repository anyway.

## About the key in the source code

`samsung_notes_export.py` contains the constant `FIXED_KEY`. It is not a personal secret. Smart Switch uses this same fixed value for all users to protect a per-backup session value in `backupHistoryInfo.xml`, and it is already public in other open-source tools, such as [smartswitch-explorer](https://github.com/sachk/smartswitch-explorer).

## How it works

1. Reads the encrypted `<Dummy>` value from `backupHistoryInfo.xml` and decrypts it with `FIXED_KEY`.
2. Takes the first 16 bytes of the SHA-256 hash of that value, which is the backup's AES key.
3. Decrypts `sdoc.bk` from `SAMSUNGNOTE/SamsungNote.SNMM`, which gives a ZIP file of notes.
4. Reads the note list and folder names from that ZIP, and extracts each note as `.sdocx`.
5. Deletes the temporary decrypted ZIP.
6. Converts each `.sdocx` to PDF with [sdocx-cli](https://github.com/twangodev/sdocx).

## Disclaimer

This is an unofficial project, not affiliated with or endorsed by Samsung. Use it only on backups of your own devices.
