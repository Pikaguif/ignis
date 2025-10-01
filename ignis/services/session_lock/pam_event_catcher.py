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

    __gtype_name__ = "IgnisPamPasswordEntry"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(self, force_keep_focus:bool, **kwargs):
        Gtk.Entry.__init__(self)
        BaseWidget.__init__(self, **kwargs)

        self.visible = True
        self.visibility = False
        self.connect("activate", lambda x: asyncio.create_task(self.check_pam_async()))
        self._pam_status = "normal"
        
        self.secondary_icon_name = "view-reveal-symbolic.symbolic"
        self.secondary_icon_activatable = True
        self.connect("icon-press",self._handle_reveal)
        
        if force_keep_focus:
            self.focus_controller = Gtk.EventControllerFocus()
            self.add_controller(self.focus_controller)
            self.focus_controller.connect("notify::contains-focus", lambda x, y: asyncio.create_task(self._keep_focus()))
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
        self._pam_status = "checking"
        self.notify("pam-status")
        
        username = os.getlogin()

        ok = pam.authenticate(username, self.get_text())

        if ok:
            self._pam_status = "success"
            self.notify("pam-status")
            self.emit("unlock-session")
        else:
            self._pam_status = "fail"
            self.notify("pam-status")
            self.delete_text(0, -1)
            utils.Timeout(ms=2_000, target=lambda: self._reset_pam_status())

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

    def _reset_pam_stauts(self):
        self._pam_status = "normal"
        self.notify("pam-status")
