"""
Pytest configuration for test directory.

This file ensures that the project root is in the Python path
so that modules can be imported correctly.
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

