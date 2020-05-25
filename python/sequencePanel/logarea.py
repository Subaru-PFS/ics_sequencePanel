__author__ = 'alefur'

import os
from datetime import datetime as dt
from functools import partial

import sequencePanel
from PyQt5.QtGui import QFont, QTextCursor
from PyQt5.QtWidgets import QPlainTextEdit, QGridLayout, QVBoxLayout
from sequencePanel.widgets import PushButton

imgpath = os.path.abspath(os.path.join(os.path.dirname(sequencePanel.__file__), '../..', 'img'))


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
