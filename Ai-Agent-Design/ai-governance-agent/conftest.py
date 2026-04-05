"""
pytest configuration — adds the project root to sys.path so that
`src`, `config`, and `scripts` imports resolve without installing the package.

This file is automatically loaded by pytest before any test collection begins.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
