from gi.repository import (
    Gtk,
    Gdk,
)


from ignis import widgets
from ignis.base_service import BaseService
from ignis.exceptions import (
    SessionLockUnsupported,
    WindowAlreadyRealized,
    WindowMisconfigured,
)
from ignis.gobject import IgnisProperty
from ignis.services.session_lock import PamPasswordEntry
from ignis.window_manager import WindowManager


from ._imports import Gtk4SessionLock as SessionLock


window_manager = WindowManager.get_default()


class SessionLockService(BaseService):
    """
    A SessionLock service.
    Allows locking and unlock your session, with password or otherwise.

    Requires 'python-pam' to verify password.

    .. warning::
        Not all desktop environments supported by most of Ignis will work with this service.
        To use this service, your compositor requires 'ext-session-lock-v1' support.
        The biggest compositor to be affected by this requirement is Kwin.

    Example usage:
    .. code-block:: python

        from ignis.services.session_lock import SessionLockService
        lock = SessionLockService.get_default()

        window = widgets.Window()
        lock.lock_session(window)
        lock.unlock_session()
    """

    def __init__(self):
        super().__init__()

        if not SessionLock.is_supported():
            raise SessionLockUnsupported() from None

        self._lock_instance = SessionLock.Instance.new()
        self._is_locked: bool = False
        self._lock_instance.connect("monitor", self._on_monitor)
        self._entry_buffer: Gtk.PasswordEntryBuffer | None = None
        self._current_monitor: int = 0

    @IgnisProperty
    def is_locked(self) -> bool:
        """
        Returns whether the session is currently locked by Ignis.
        Can be set to lock/unlock the session.
        """
        return self._is_locked

    @is_locked.setter
    def is_locked(self, locked: bool) -> None:
        if locked and not self._lock_instance.is_locked():
            self._lock_instance.lock_session()
        elif not locked and self._lock_instance.is_locked():
            self._lock_instance.unlock_session()

    def lock_session(self, window: type[widgets.Window]):
        """
        Locks the session.

        Args:
            window: widgets.Window class constructor (not an instance of one). The given window must be unrealized (usually, making the window not visible by default is enough).
        """
        if not self._lock_instance.is_locked() and self._test_window(window):
            self._focused_window = window
            self._entry_buffer = Gtk.PasswordEntryBuffer()
            self._lock_instance.lock()
            self.notify("is-locked")
            self._current_monitor += 1

    def unlock_session(self, *_):
        """
        Unlocks the session, removing all instantiated windows with lock_session().
        """
        if self._lock_instance.is_locked():
            self._lock_instance.unlock()
            self._entry_buffer = None
            self.notify("is-locked")
            self._current_monitor = 0

    def add_password_entry_child(
        self, use_common_buffer: bool = False, force_keep_focus: bool = False, **kwargs
    ) -> PamPasswordEntry:
        """
        Returns a PamPasswordEntry widget

        Args:
            use_common_buffer: Whether to use a single buffer for all instances of PamPasswordEntry. This means the text typed will be shared with all instances
            force_keep_focus: Whether the widget should keep keyboard focus at all times.
        """
        password_entry = PamPasswordEntry(force_keep_focus=force_keep_focus, **kwargs)
        password_entry.connect("unlock-session", self.unlock_session)
        if use_common_buffer:
            password_entry.buffer = self._entry_buffer
        else:
            password_entry.buffer = Gtk.PasswordEntryBuffer()

        return password_entry

    def _on_monitor(self, lock: SessionLock.Instance, monitor: Gdk.Monitor):
        win = self._focused_window()  # type: ignore
        window_manager.remove_window(win.namespace)

        self._lock_instance.assign_window_to_monitor(win, monitor)

    def _test_window(self, test_window: type[widgets.Window]) -> bool:
        try:
            win = test_window()  # type: ignore
            # Mypy is ignored for this line because it really wants a namespace.
            # Any user should provide a namespace on their own to any window they use.
            # But, providing a namespace to an already define window (expected use case),
            # will cause an error, that does not happen with this line.
            #
            # To ensure that no-one forgets the namespace, this is already in a try
            # statement, to be able to correctly unlock the session, and avoid a
            # permanently locked session that happens when the code breaks.
        except TypeError:
            raise WindowMisconfigured from None

        window_manager.remove_window(win.namespace)
        if win.visible:
            raise WindowAlreadyRealized() from None

        win.unrealize()
        return True
