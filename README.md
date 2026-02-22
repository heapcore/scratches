# scratches

> **WARNING:** This repository may be unstable or non-functional. Use at your own risk.

Collection of small utilities, programming exercises, and experiments.

## Project Structure

```
scratches/
├── scripts/       # utility scripts (Python + shell)
├── algorithms/    # algorithm tasks
├── experiments/   # concurrency and small coding exercises
└── games/         # simple game implementations
```

## Script Catalog (`scripts/`)

### Project maintenance
- `audit_project_files.py` - Audits top-level projects in `Legacy` for git default branch, formatting problems, and README requirements.
- `check_non_latin_letters.py` - Scans projects for non-Latin characters in text files.

### API and connectivity
- `claude_api_check.py` - Diagnostic check for Anthropic API access (Cloudflare trace + test request).
- `claude_list_models.py` - Prints available Anthropic models using API key.
- `github_api.py` - Legacy GitHub repository analyzer (contributors, pulls, issues).

### File and media processing
- `convert_ffmpeg.py` - Batch video conversion via `ffmpeg` (size presets and CRF).
- `scale_images.sh` - Batch image resize/conversion workflow (expects ImageMagick tooling).
- `compress_7z.sh` - Compresses `.tif` files into `.7z` archives.
- `compile_djvu.sh` - Builds a DjVu book from `.tif`/`.djvu` pages.
- `delete_files.sh` - Deletes `.jpg` files listed in a text file.
- `jpg_to_pdf.py` - Creates one or more PDFs from lists of JPG files (Pillow).
- `pdf_handler.py` - Helper class for merging/stamping PDF pages (PyPDF2 + reportlab).
- `docx_handler.py` - Template text replacement in DOCX files (python-docx, Python 2 style code).

### Text and data helpers
- `counter.py` - Word frequency counter for text files.
- `gen_hardcoded_query.py` - Converts SQL `INSERT ... VALUES (...)` rows into `SELECT ... UNION ALL`.
- `gmail_mbox_parser.py` - Parses Gmail MBOX exports and prints sender/recipient stats.
- `tk_file_deleter.py` - Tkinter GUI helper for file deletion.

## Other Folders

### `algorithms/`
- Sorting, list merge, matrix operations, tree serialization, and knapsack variants.

### `experiments/`
- Single-thread, multi-thread, and multiprocessing examples.
- Additional exercises such as session/cart simulation and percentage calculations.
- `delete_routes.bat` for route cleanup on Windows.

### `games/`
- `connect4.py` and `test_connect4.py`.

## Usage Examples

```bash
# scan all Legacy projects for non-Latin characters
python scripts/check_non_latin_letters.py

# scan specific folders only
python scripts/check_non_latin_letters.py scratches django_chatbot

# audit project formatting/README/git defaults across Legacy
python scripts/audit_project_files.py

# Anthropic API diagnostics (direct key)
python scripts/claude_api_check.py --api-key <KEY>

# Anthropic API diagnostics (from environment)
set ANTHROPIC_API_KEY=<KEY>
python scripts/claude_api_check.py --model claude-sonnet-4-5-20250929 --message "ping"

# list Anthropic models
python scripts/claude_list_models.py <KEY>

# top word frequencies (script currently uses hardcoded input file)
python scripts/counter.py

# parse Gmail MBOX export (path currently hardcoded in script)
python scripts/gmail_mbox_parser.py

# convert media with ffmpeg presets (paths configured in script)
python scripts/convert_ffmpeg.py

# create PDFs from JPG groups (file list configured in script)
python scripts/jpg_to_pdf.py

# play Connect 4
python games/connect4.py

# run Connect 4 tests
python games/test_connect4.py

# compare concurrency approaches
python experiments/single_thread.py
python experiments/multithread.py
python experiments/multiprocessing.py
```

### Shell Script Examples

```bash
# batch resize/convert images
bash scripts/scale_images.sh

# compress tif files to 7z
bash scripts/compress_7z.sh

# build djvu book from tif files
bash scripts/compile_djvu.sh

# delete jpg files from list in dfiles
bash scripts/delete_files.sh
```

### Legacy Utility Examples

```bash
# transform SQL INSERT rows into SELECT ... UNION ALL
python scripts/gen_hardcoded_query.py input.sql

# add extra fixed columns while converting
python scripts/gen_hardcoded_query.py input.sql created_at:sysdate source:'legacy'

# run GitHub repository analyzer
# note: token and defaults are configured inside the script
python scripts/github_api.py --url https://github.com/<owner>/<repo> --branch main
```

## Notes

- Some scripts are modern Python 3, others are legacy snippets and may require adaptation.
- External tools/libraries used by some scripts:
  - `ffmpeg`
  - `7z`
  - DjVu utils (`cjb2`, `djvm`)
  - Python packages such as `requests`, `beautifulsoup4`, `lxml`, `Pillow`, `PyPDF2`, `reportlab`, `python-docx`

## License

See `LICENSE`.
