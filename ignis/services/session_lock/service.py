from ctypes import CDLL
CDLL('libgtk4-layer-shell.so')

import gi
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gtk4SessionLock as SessionLock

from ignis.gobject import IgnisProperty, IgnisSignal
from ignis.base_service import BaseService
from ignis import widgets
from ignis.window_manager import WindowManager

from ignis.services.session_lock import PamPasswordEntry

window_manager = WindowManager.get_default()

class SessionLockService(BaseService):

    def __init__(self):
        super().__init__()
        self._lock_instance = SessionLock.Instance.new()
        self._is_locked: bool  = False
        self._entry_buffer: Gtk.PasswordEntryBuffer | None = None
        self._lock_instance.connect('monitor', self._on_monitor) #Testing

    @IgnisProperty
    def is_locked(self):
        return self._is_locked

    @is_locked.setter
    def is_locked(
        self, 
        locked: bool
    ) -> None:
        if locked and not self._lock_instance.is_locked():
            self._lock_instance.lock()
        elif not locked and self._lock_instance.is_locked():
            self._lock_instance.unlock()

    def lock_session(self, window):
        if not self._lock_instance.is_locked():
            self._focused_window = window
            self._entry_buffer = Gtk.PasswordEntryBuffer()
            self._lock_instance.lock()

    def unlock_session(self, *_):
        if self._lock_instance.is_locked():
            self._lock_instance.unlock()
            self._entry_buffer = None

    def add_password_entry_child(self, **kwargs) -> PamPasswordEntry:
        password_entry = PamPasswordEntry(**kwargs)
        password_entry.connect("unlock-session",self.unlock_session)
        password_entry.buffer = self._entry_buffer
        
        return password_entry

    def _on_monitor(self, lock, monitor):
        win = self._focused_window("lockwindow"+monitor.get_connector())
            
        self._lock_instance.assign_window_to_monitor(win, monitor)
