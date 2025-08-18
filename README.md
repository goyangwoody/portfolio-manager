How to make imports work in this repo

Options provided in this repository:

1) Editable install (recommended)
   - From repo root (`c:\Users\Seungjae\Desktop\pr`) run:
     ```powershell
     pip install -e .
     ```
   - This installs packages under `src/` (for example `pm`) in editable mode so `import pm` works everywhere.

2) Run as a module (no install)
   - From repo root run:
     ```powershell
     python -m src.scripts.gui_transaction_input
     ```
   - This ensures Python treats `src` as package root.

3) Set PYTHONPATH (temporary)
   - In PowerShell:
     ```powershell
     $env:PYTHONPATH = "${PWD}\src"
     python src/scripts/gui_transaction_input.py
     ```

4) VS Code helper
   - `.vscode/settings.json` in this repo sets `python.analysis.extraPaths` to `${workspaceFolder}/src` and terminal PYTHONPATH so the editor and integrated terminal see `src`.

If you want, I can run `pip install -e .` here to verify and run a quick import test. Paste any error trace if it still fails.
"# portfolio-manager" 
