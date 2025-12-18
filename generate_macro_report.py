#!/usr/bin/env python3
"""
generate_macro_report.py (wrapper)

Thin wrapper that keeps the historical CLI entrypoint stable while the
implementation lives in `src/macro_econ_data_archive/report_generator.py`.
"""

from __future__ import annotations

from pathlib import Path
import sys


def _ensure_src_on_path() -> None:
    repo_root = Path(__file__).resolve().parent
    src_dir = repo_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))


def main() -> int:
    _ensure_src_on_path()
    from macro_econ_data_archive.report_generator import main as impl_main

    return impl_main()


if __name__ == "__main__":
    raise SystemExit(main())

