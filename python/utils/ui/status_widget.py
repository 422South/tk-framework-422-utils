# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'status-widget.ui'
##
## Created by: Qt User Interface Compiler version 5.15.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

# from PySide2.QtCore import *
# from PySide2.QtGui import *
# from PySide2.QtWidgets import *

# from tank.platform.qt import QtCore, QtGui, QtWidgets
from sgtk.platform.qt import QtCore, QtGui

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(400, 140)
        Dialog.setMinimumSize(QtCore.QSize(400, 140))
        Dialog.setAutoFillBackground(False)
        self.progressBar = QtGui.QProgressBar(Dialog)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setGeometry(QtCore.QRect(30, 90, 341, 23))
        self.progressBar.setValue(0)
        self.InfoLabel = QtGui.QLabel(Dialog)
        self.InfoLabel.setObjectName(u"InfoLabel")
        self.InfoLabel.setGeometry(QtCore.QRect(30, 60, 341, 21))

        self.retranslateUi(Dialog)

        QtCore.QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtCore.QCoreApplication.translate("Dialog", u"Cloud Status", None))
        self.InfoLabel.setText(QtCore.QCoreApplication.translate("Dialog", u"TextLabel", None))
    # retranslateUi
