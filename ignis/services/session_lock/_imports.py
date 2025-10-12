import gi

from ignis.exceptions import PythonPAMNotFound
from ignis import is_sphinx_build

try:
    if not is_sphinx_build:
        gi.require_version("Gtk4SessionLock", "1.0")
    from gi.repository import Gtk4SessionLock #type: ignore
    import pam  # type: ignore
except (ImportError, ValueError):
    raise PythonPAMNotFound() from None

__all__ = ["pam", "Gtk4SessionLock"]
