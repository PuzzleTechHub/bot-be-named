"""Root conftest to configure Python path for tests."""

from __future__ import annotations

import sys
from pathlib import Path

# Add the project root to sys.path so imports work correctly
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
