from ctypes import CDLL
CDLL('libgtk4-layer-shell.so')

import gi
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gtk4SessionLock as SessionLock
from ignis.gobject import IgnisProperty, IgnisSignal

from ignis.base_service import BaseService
from ignis import widgets

class SessionLockService(BaseService):

    def __init__(self):
        super().__init__()
        self._lock_instance = SessionLock.Instance.new()
        self._is_locked: bool  = False #It should always be locked when the session lock is created
        self._focused_window: widgets.Window | None  = None

        self._lock_instance.connect('monitor', self._on_monitor) #Testing

    @IgnisProperty
    def is_locked(self):
        return self._is_locked

    def lock_session(self):
        self._lock_instance.lock()
        print(self._lock_instance.is_locked())

    def unlock_session(self):
        self._lock_instance.unlock()
        print(self._lock_instance.is_locked())

    #Testing - To be removed prior to PR
    def _on_monitor(self, lock_instance, monitor):
        window = Gtk.Window()

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_halign(Gtk.Align.CENTER)
        box.set_valign(Gtk.Align.CENTER)
        window.set_child(box)

        label = Gtk.Label(label="GTK Session Lock with Python")
        box.append(label)

        button = Gtk.Button(label='Unlock')
        button.connect('clicked', self._on_unlock_clicked)
        box.append(button)

        self._lock_instance.assign_window_to_monitor(window, monitor)

    def _on_unlock_clicked(self, button):
        self._lock_instance.unlock()
