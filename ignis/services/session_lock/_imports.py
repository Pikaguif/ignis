import gi
import sys
from ignis.exceptions import GvcNotFoundError
from ignis import is_sphinx_build

# Gvc is here just for example.
try:
    if not is_sphinx_build:  
        gi.require_version("pam", "2.0.2")
        gi.require_version("six", "1.17.0")
    import pam  # type: ignore
except (ImportError, ValueError):
    raise GvcNotFoundError() from None

__all__ = ["pam"]
