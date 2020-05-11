__author__ = 'alefur'

import os
import time

import numpy as np
import yaml
from PyQt5.QtWidgets import QGridLayout, QWidget, QLineEdit, QAction, QMenuBar, QFileDialog
from sequencePanel.dialog import Dialog
from sequencePanel.scheduler import Scheduler
from sequencePanel.sequence import CmdRow
from sequencePanel.table import Table
from sequencePanel.widgets import CmdLogArea


class MouseMove(object):
    timeout = 5

    def __init__(self, x, y):
        self.t = time.time()
        self.x = x
        self.y = y

    @property
    def userInactive(self):
        return (time.time() - self.t) > MouseMove.timeout

    def checkPosition(self, x, y):
        if not (self.x == x and self.y == y):
            self.x = x
            self.y = y
            self.t = time.time()


class PanelWidget(QWidget):
    def __init__(self, mwindow):
        self.printLevels = {'D': 0, '>': 0,
                            'I': 1, ':': 1,
                            'W': 2,
                            'F': 3, '!': 4}
        self.printLevel = self.printLevels['I']
        self.cmdRows = []
        self.mouseMove = MouseMove(0, 0)

        QWidget.__init__(self)
        self.mwindow = mwindow

        self.mainLayout = QGridLayout()
        self.scheduler = Scheduler(self)
        self.logLayout = QGridLayout()

        self.menuBar = self.createMenu()
        self.sequenceTable = Table(self)

        self.commandLine = QLineEdit()
        self.commandLine.returnPressed.connect(self.sendCmdLine)

        self.logArea = CmdLogArea()
        self.logLayout.addWidget(self.logArea, 0, 0, 10, 1)
        self.logLayout.addWidget(self.commandLine, 10, 0, 1, 1)

        self.mainLayout.addWidget(self.menuBar, 0, 0, 1, 10)
        self.mainLayout.addWidget(self.sequenceTable, 1, 0, 35, 10)
        self.mainLayout.addLayout(self.scheduler, 36, 0, 4, 4)

        self.mainLayout.addLayout(self.logLayout, 40, 0, 25, 10)

        self.setMinimumWidth(920)
        self.setLayout(self.mainLayout)
        self.setMouseTracking(True)

    @property
    def actor(self):
        return self.mwindow.actor

    @property
    def currInd(self):
        areActive = [cmdRow.isActive for cmdRow in self.cmdRows]
        if not True in areActive:
            return False
        else:
            return np.argmax(areActive) + 1

    def addSequence(self):
        d = Dialog(self)

    def add(self, cmdRow):
        self.cmdRows.append(cmdRow)
        self.updateTable()

    def insert(self, index, cmdRow):
        self.cmdRows.insert(index, cmdRow)
        self.updateTable()

    def updateTable(self):

        scrollvalue = self.sequenceTable.verticalScrollBar().value()

        self.sequenceTable.hide()
        self.sequenceTable.close()
        self.sequenceTable.deleteLater()
        self.mainLayout.removeWidget(self.sequenceTable)

        self.sequenceTable = Table(self)
        self.mainLayout.addWidget(self.sequenceTable, 1, 0, 35, 10)

        self.sequenceTable.verticalScrollBar().setScrollValue(value=scrollvalue)

    def sendCmdLine(self):
        self.sendCommand(fullCmd=self.commandLine.text())

    def sendCommand(self, fullCmd, timeLim=300, callFunc=None):
        callFunc = self.logArea.printResponse if callFunc is None else callFunc

        import opscore.actor.keyvar as keyvar

        try:
            [actor, cmdStr] = fullCmd.split(' ', 1)
        except ValueError:
            return

        self.logArea.newLine('cmdIn=%s %s' % (actor, cmdStr))
        self.actor.cmdr.bgCall(**dict(actor=actor,
                                      cmdStr=cmdStr,
                                      timeLim=timeLim,
                                      callFunc=callFunc,
                                      callCodes=keyvar.AllCodes))

    def createMenu(self):
        menubar = QMenuBar(self)
        fileMenu = menubar.addMenu('File')
        addMenu = menubar.addMenu('Add')
        editMenu = menubar.addMenu('Edit')

        loadSequence = QAction('Open', self)
        loadSequence.triggered.connect(self.loadFile)
        loadSequence.setShortcut('Ctrl+O')

        saveSequence = QAction('Save', self)
        saveSequence.triggered.connect(self.saveFile)
        saveSequence.setShortcut('Ctrl+S')

        addSequence = QAction('New Sequence', self)
        addSequence.triggered.connect(self.addSequence)

        selectAll = QAction('Select All', self)
        selectAll.triggered.connect(self.selectAll)
        selectAll.setShortcut('Ctrl+A')

        clearDone = QAction('Clear Done', self)
        clearDone.triggered.connect(self.clearDone)

        fileMenu.addAction(loadSequence)
        fileMenu.addAction(saveSequence)

        addMenu.addAction(addSequence)

        editMenu.addAction(selectAll)
        editMenu.addAction(clearDone)

        return menubar

    def loadFile(self):
        filepath, fmt = QFileDialog.getOpenFileName(self, 'Open File', '/home/', "(*.yaml)")
        if not filepath:
            return

        try:
            with open(os.path.expandvars(filepath), 'r') as cfgFile:
                cmdRows = yaml.load(cfgFile, Loader=yaml.FullLoader)

        except PermissionError as e:
            self.mwindow.showError(str(e))
            return

        for i, kwargs in cmdRows.items():
            self.add(CmdRow(self, **kwargs))

    def saveFile(self):

        if not self.cmdRows:
            self.mwindow.showError('Your script is empty...')
            return

        seq = dict([(i, cmdRow.info) for i, cmdRow in enumerate(self.cmdRows)])

        try:

            filepath, fmt = QFileDialog.getSaveFileName(self, 'Save File',
                                                        f'/home/script.yaml', "(*.yaml)")
            if filepath:
                with open(os.path.expandvars(filepath), 'w') as savedFile:
                    yaml.dump(seq, savedFile)

        except PermissionError as e:
            self.mwindow.showError(str(e))

    def selectAll(self):
        self.sequenceTable.selectAll()

    def copy(self, cmdRows):
        self.clipboard = [cmdRow.info for cmdRow in cmdRows]

    def paste(self, ind):
        newSeq = [CmdRow(self, **kwargs) for kwargs in self.clipboard]
        self.cmdRows[ind:ind] = newSeq
        self.updateTable()

    def remove(self, cmdRows):
        for cmdRow in cmdRows:
            if not cmdRow in self.cmdRows:
                continue

            self.cmdRows.remove(cmdRow)
        self.updateTable()

    def clearDone(self):
        cmdRows = [cmdRow for cmdRow in self.cmdRows if cmdRow.status in ['finished', 'failed']]
        self.remove(cmdRows)

    def mouseMoveEvent(self, event):
        self.mouseMove.checkPosition(x=event.x(), y=event.y())
        QWidget.mouseMoveEvent(self, event)

    def resizeEvent(self, event):
        QWidget.resizeEvent(self, event)
        self.sequenceTable.resizeEvent(event)
