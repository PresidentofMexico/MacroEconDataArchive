#!/usr/bin/env python3
"""
app.py (wrapper)

Thin wrapper to keep `streamlit run app.py` working while the implementation
lives in `src/macro_econ_data_archive/streamlit_app.py`.
"""

from __future__ import annotations

from pathlib import Path
import sys


def _ensure_src_on_path() -> None:
    repo_root = Path(__file__).resolve().parent
    src_dir = repo_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))


def main() -> None:
    _ensure_src_on_path()
    from macro_econ_data_archive.streamlit_app import main as impl_main

    impl_main()


if __name__ == "__main__":
    main()

