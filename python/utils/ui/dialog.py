
# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.
import sys
# sys.path.insert(0, "/Users/craighowarth/ShotgunDev/tk-drain_clone/install/core/python/sgtk")
import sgtk
import os
import time

import threading

# by importing QT from sgtk rather than directly, we ensure that
# the code will be compatible with both PySide and PyQt.

from sgtk.platform.qt import QtCore, QtGui
from .status_widget import Ui_Dialog

# standard toolkit logger
logger = sgtk.platform.get_logger(__name__)


# def show_dialog(app_instance):
#     """
#     Shows the main dialog window.
#     """
#     # in order to handle UIs seamlessly, each toolkit engine has methods for launching
#     # different types of windows. By using these methods, your windows will be correctly
#     # decorated and handled in a consistent fashion by the system.
#
#     # we pass the dialog class to this method and leave the actual construction
#     # to be carried out by toolkit.
#     app_instance.engine.show_dialog("Starter Template App...", app_instance, AppDialog)

def show_dialog():
    m = AppDialog()
    m.show()
    return m


class AppDialog(QtGui.QWidget):
    """
    Main application dialog window
    """

    def __init__(self):
        """
        Constructor
        """
        # first, call the base class and let it do its thing.
        QtGui.QWidget.__init__(self)

        # now load in the UI that was created in the UI designer
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        # most of the useful accessors are available through the Application class instance
        # it is often handy to keep a reference to this. You can get it via the following method:
        # self._app = sgtk.platform.current_bundle()

        # logging happens via a standard toolkit logger
        # logger.info("Launching Starter Application...")

        # via the self._app handle we can for example access:
        # - The engine, via self._app.engine
        # - A Shotgun API instance, via self._app.shotgun
        # - An Sgtk API instance, via self._app.sgtk

        # lastly, set up our very basic UI
        # self.ui.context.setText("Current Context: %s" % self._app.context)

    if __name__ == "__main__":
        app = QtGui.QApplication.instance()
        window = show_dialog()
        app.exec_()

    def updateLabel(self, text):
        self.ui.InfoLabel.setText(text)

    def updateProgress(self, value):
        self.ui.progressBar.setValue(value)

    def closeUI(self):
        self.close()


"""
    import dialog
    dialog.show_dialog()
"""