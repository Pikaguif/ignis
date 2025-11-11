from gi.repository import Gtk

from ignis import utils
from ignis.base_widget import BaseWidget
from ignis.gobject import IgnisProperty, IgnisSignal

from ._imports import pam
import os
import asyncio


class PamPasswordEntry(Gtk.Entry, BaseWidget): # type: ignore
    """
    An specialized Entry widget.
    Includes methods to verify, authenticate and unlock session.

    Requires 'python-pam'

    Example usage:
    .. code-block:: python

        from ignis.services.session_lock import SessionLockService
        lock = SessionLockService.get_default()

        window = widgets.Window()
        lock.lock_session(window)
        window.set_child(add_password_entry_child())
    """

    __gtype_name__ = "IgnisPamPasswordEntry"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(self, force_keep_focus: bool = False, **kwargs):
        Gtk.Entry.__init__(self)
        BaseWidget.__init__(self, **kwargs)

        # Setup PAM
        self.connect("activate", lambda x: asyncio.create_task(self.check_pam_async()))
        self._pam_status = "normal"

        # Setup PasswordEntry behavior
        self.secondary_icon_name = "view-reveal-symbolic.symbolic"
        self.secondary_icon_activatable = True
        self.connect("icon-press", self._handle_reveal)
        self.visibility = False

        # Note that the class for the buffer is Gtk.PasswordEntryBuffer as well since
        # the SessionLockService function changes it to that.
        if force_keep_focus:
            self.focus_controller = Gtk.EventControllerFocus()
            self.add_controller(self.focus_controller)
            self.focus_controller.connect(
                "notify::contains-focus",
                lambda x, y: asyncio.create_task(self._keep_focus()),
            )
            # This HAS to be async, if not, GTK tries to give focus to two widgets at once, and focus breaks.
            self.grab_focus()

    @IgnisSignal
    def unlock_session(self):
        """
        Emitted when PAM verification passes and session is unlocked.
        """

    @IgnisProperty
    def pam_status(self) -> str:
        """
        Returns the status of the PAM verification. Can have one of the following values:
            - normal
            - success
            - fail
            - checking
        """
        return self._pam_status

    async def check_pam_async(self):
        """
        Checks whether the password currently typed is correct.
        This function is triggered automatically on pressing activating the entry.
        """

        self._pam_status = "checking"
        self.notify("pam-status")

        username = (
            os.getlogin()
        )  # The python docs recommend another method since this is slower,
        # but given the other method can be "confused" to give a value it shouldn't, this seems
        # better for password verification.

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
