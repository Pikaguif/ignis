from gi.repository import Gtk
from ignis import utils
from ignis.base_widget import BaseWidget
from ignis.gobject import IgnisProperty, IgnisSignal
from ignis.widgets import Entry
import pam
import os
import asyncio

class PamPasswordEntry(Gtk.PasswordEntry, BaseWidget):

    def __init__(self, **kwargs):
        Gtk.PasswordEntry.__init__(self)
        BaseWidget.__init__(self, **kwargs)

        self._pam_status = "normal"

        self.connect("activate", lambda x: asyncio.create_task(self.check_pam_async()))

        self.grab_focus()
    
    @IgnisSignal
    def unlock_session(self):
        """
        Emitted when PAM verification passes and session is unlocked.
        """
        
    @IgnisProperty
    def pam_status(self):
        return self._pam_status

    async def check_pam_async(self):
        username = os.getlogin()

        self._pam_status = "checking"

        ok = pam.authenticate(username, self.get_text())

        if ok:
            self.emit("unlock-session")
        else:
            self.delete_text(0, -1)
