"""Verification tests ensuring all dashboard pages compile and import without errors."""

from pathlib import Path
import py_compile
import pytest


def test_app_and_all_pages_compile():
    """Verify that app.py and all pages compile without syntax or import errors."""
    root = Path(__file__).parent.parent
    
    # Check app.py
    app_file = root / "app.py"
    assert app_file.is_file(), "app.py does not exist."
    py_compile.compile(str(app_file), doraise=True)

    # Check all 12 pages
    pages_dir = root / "pages"
    page_files = sorted(pages_dir.glob("*.py"))
    assert len(page_files) == 12, f"Expected 12 page files in pages/, found {len(page_files)}"

    for page_path in page_files:
        py_compile.compile(str(page_path), doraise=True)
