from gi.repository import Gtk 
from gi.repository.GdkPixbuf import Pixbuf

from ignis import utils
from ignis.base_widget import BaseWidget
from ignis.gobject import IgnisProperty, IgnisSignal
from ignis.widgets import Entry

import pam
import os
import asyncio

class PamPasswordEntry(Gtk.Entry, BaseWidget):

    def __init__(self, **kwargs):
        Gtk.Entry.__init__(self)
        BaseWidget.__init__(self, **kwargs)

        self.visible = True
        self.visibility = False
        self.connect("activate", lambda x: asyncio.create_task(self.check_pam_async()))
        self._pam_status = "normal"
        
        self.secondary_icon_name = "view-reveal-symbolic.symbolic"
        self.secondary_icon_activatable = True
        self.connect("icon-press",self._handle_reveal)

        self.focus_controller = Gtk.EventControllerFocus()
        self.add_controller(self.focus_controller)
        self.focus_controller.connect("notify::contains-focus", lambda x, y: asyncio.create_task(self._keep_focus()))
    
    @IgnisSignal
    def unlock_session(self):
        """
        Emitted when PAM verification passes and session is unlocked.
        """
        
    @IgnisProperty
    def pam_status(self):
        return self._pam_status

    async def check_pam_async(self):
        print("Checking PAM")
        username = os.getlogin()

        self._pam_status = "checking"

        ok = pam.authenticate(username, self.get_text())

        if ok:
            self.emit("unlock-session")
        else:
            self.delete_text(0, -1)

    def _handle_reveal(self, entry, pos):
        
        if not pos:
            return

        if self.visibility:
            self.secondary_icon_name = "view-reveal-symbolic.symbolic"
            self.visibility = False
        else:
            self.secondary_icon_name = "view-conceal-symbolic.symbolic"
            self.visibility = True

    async def _keep_focus(self, *_):
        if not self.focus_controller.contains_focus():
            self.grab_focus_without_selecting()
