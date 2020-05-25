__author__ = 'alefur'

import os
from datetime import datetime as dt
from functools import partial

import sequencePanel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon, QFont, QTextCursor
from PyQt5.QtWidgets import QPushButton, QSpinBox, QComboBox, QLineEdit, QLabel, QPlainTextEdit, QProgressBar, \
    QGridLayout, QVBoxLayout

imgpath = os.path.abspath(os.path.join(os.path.dirname(sequencePanel.__file__), '../..', 'img'))


class Label(QLabel):
    def __init__(self, *args, **kwargs):
        QLabel.__init__(self, *args, **kwargs)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(
            """QLabel { border-style: outset;border-width: 2px;border-radius: 7px;border-color: beige;font: bold 8pt; padding: 3px;}""")


class WhiteLabel(QLabel):
    def __init__(self, *args, **kwargs):
        QLabel.__init__(self, *args, **kwargs)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(
            "QLabel { background-color : white; color : black; qproperty-alignment: AlignCenter; font: 8pt; border-radius: 7px;padding: 3px;}")


class ComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        QComboBox.__init__(self, *args, **kwargs)
        self.setStyleSheet("QComboBox { font: 8pt;}")


class LineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        QLineEdit.__init__(self, *args, **kwargs)
        self.setStyleSheet("QLineEdit { font: 8pt;}")


class SpinBox(QSpinBox):
    def __init__(self, *args, **kwargs):
        QSpinBox.__init__(self, *args, **kwargs)
        self.setStyleSheet("QSpinBox { font: 8pt;}")


class PushButton(QPushButton):
    def __init__(self, label=''):
        QPushButton.__init__(self, label)
        self.setStyleSheet("QPushButton {font: 8pt; }")


class CLabel(QLabel):
    colors = {"ON": ('green', 'white'),
              "OFF": ('red', 'white'),
              "WAITING": ('blue', 'white'),
              "PROCESSING": ('green', 'white')
              }

    def __init__(self, txt):
        QLabel.__init__(self)
        self.setText(txt=txt)

    def setColor(self, background, police='white'):
        if background == "red":
            self.setStyleSheet(
                "QLabel {font-size: 9pt; qproperty-alignment: AlignCenter; color:%s; background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #f43131, stop: 1 #5e1414); border: 1px solid gray;border-radius: 3px;}" % police)
        elif background == "green":
            self.setStyleSheet(
                "QLabel {font-size: 9pt; qproperty-alignment: AlignCenter; color:%s; background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #45f42e, stop: 1 #195511); border: 1px solid gray;border-radius: 3px;}" % police)
        elif background == "blue":
            self.setStyleSheet(
                "QLabel {font-size: 9pt; qproperty-alignment: AlignCenter; color:%s; background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #3168f4, stop: 1 #14195e); border: 1px solid gray;border-radius: 3px;}" % police)
        elif background == "yellow":
            self.setStyleSheet(
                "QLabel {font-size: 9pt; qproperty-alignment: AlignCenter; color:%s; background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #edf431, stop: 1 #5e5b14); border: 1px solid gray;border-radius: 3px;}" % police)
        elif background == "orange":
            self.setStyleSheet(
                "QLabel {font-size: 9pt; qproperty-alignment: AlignCenter; color:%s; background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #f4a431, stop: 1 #5e4a14); border: 1px solid gray;border-radius: 3px;}" % police)

    def setText(self, txt):
        try:
            background, police = CLabel.colors[txt]
            self.setColor(background=background, police=police)
        except KeyError:
            pass

        QLabel.setText(self, txt)


class LogLayout(QVBoxLayout):
    def __init__(self, panelwidget):
        QGridLayout.__init__(self)
        self.panelwidget = panelwidget
        self.logArea = CmdLogArea()

        self.showButton = PushButton('Show Logs')
        self.hideButton = PushButton('Hide Logs')
        self.showButton.clicked.connect(partial(self.show, True))
        self.hideButton.clicked.connect(partial(self.show, False))

        self.panelwidget.scheduler.addWidget(self.showButton, 1, 10)
        self.panelwidget.scheduler.addWidget(self.hideButton, 1, 11)
        self.addWidget(self.logArea)
        self.show(False)

    def show(self, bool):
        width, height = self.panelwidget.width(), self.panelwidget.height()
        try:
            scrollValue = self.panelwidget.sequenceTable.verticalScrollBar().value()
        except:
            scrollValue = 0

        offset = self.logArea.fixedHeight + 5
        height += (offset if bool else -offset)
        self.showButton.setVisible(not bool)
        self.hideButton.setVisible(bool)
        self.logArea.setVisible(bool)
        self.panelwidget.adjust(width, height, scrollValue)


class CmdLogArea(QPlainTextEdit):
    printLevels = {'D': 0, '>': 0,
                   'I': 1, ':': 1,
                   'W': 2,
                   'F': 3, '!': 4}
    colorCode = {'d': '#FFFFFF',
                 '>': '#FFFFFF',
                 'i': '#FFFFFF',
                 ':': '#7FFF00',
                 'w': '#ffab50',
                 'f': '#FF0000',
                 '!': '#FF0000', }
    fixedHeight = 190

    def __init__(self):
        QPlainTextEdit.__init__(self)
        self.setMinimumSize(720, 180)
        self.printLevel = CmdLogArea.printLevels['I']
        self.setMaximumBlockCount(10000)
        self.setReadOnly(True)

        self.setStyleSheet("background-color: black;color:white;")
        self.setFont(QFont("Monospace", 8))
        self.setFixedHeight(CmdLogArea.fixedHeight)

    def newLine(self, newLine, code=None):
        code = 'i' if code is None else code
        color = CmdLogArea.colorCode[code]
        self.appendHtml('\n<font color="%s">%s  %s</font>' % (color, dt.now().strftime('%Y-%m-%d %H:%M:%S'), newLine))

        self.moveCursor(QTextCursor.End)
        self.ensureCursorVisible()

    def formatResponse(self, actor, code, keywords):
        color = CmdLogArea.colorCode[code]
        return '<font color="%s">%s %s %s</font>' % (color, actor, code, keywords)

    def printResponse(self, resp):
        reply = resp.replyList[-1]
        code = resp.lastCode

        if CmdLogArea.printLevels[code] >= self.printLevel:
            self.newLine(newLine='%s %s %s ' % (reply.header.actor,
                                                reply.header.code.lower(),
                                                reply.keywords.canonical(delimiter=';')),
                         code=reply.header.code.lower())


class ProgressBar(QProgressBar):
    def __init__(self, *args, **kwargs):
        QProgressBar.__init__(self, *args, **kwargs)
        self.setStyleSheet("QProgressBar { font: 8pt;}")


class IconButton(QPushButton):
    def __init__(self, iconFile):
        QPushButton.__init__(self)
        pix = QPixmap()
        pix.load('%s/%s' % (imgpath, iconFile))
        icon = QIcon(pix)
        self.setIcon(icon)


class EyeButton(QPushButton):
    def __init__(self):
        QPushButton.__init__(self)
        pixon = QPixmap()
        pixon.load('%s/%s' % (imgpath, 'eye_on.png'))
        self.icon_on = QIcon(pixon)

        pixon = QPixmap()
        pixon.load('%s/%s' % (imgpath, 'eye_off.png'))
        self.icon_off = QIcon(pixon)

        self.setState(False)
        self.setEnabled(False)

    def setState(self, state):
        icon = self.icon_on if not state else self.icon_off
        self.setIcon(icon)
        self.state = state
