"""Shared test configuration.

Redirect the Loyverse config directory to an isolated temp location for the
whole session so tests never read from or write to the real ``~/.loyverse``.
This must happen at import time, before ``loyverse_sdk.core.config`` is first
imported (which loads the env file and runs legacy migration on import).
"""

import os
import tempfile

_test_root = tempfile.mkdtemp(prefix="loyverse-test-")

os.environ.setdefault(
    "LOYVERSE_CONFIG_DIR",
    os.path.join(_test_root, "config"),
)
# Keep the init pointer file out of the real ~/.config during tests.
os.environ.setdefault(
    "XDG_CONFIG_HOME",
    os.path.join(_test_root, "xdg"),
)
