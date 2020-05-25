__author__ = 'alefur'

import os

import numpy as np
from functools import partial
import yaml
from PyQt5.QtWidgets import QGridLayout, QWidget, QLineEdit, QAction, QMenuBar, QFileDialog, QVBoxLayout
from sequencePanel.dialog import Dialog
from sequencePanel.scheduler import Scheduler
from sequencePanel.sequence import CmdRow
from sequencePanel.table import Table
from sequencePanel.widgets import LogLayout
from sequencePanel.annotate import Annotate

class PanelWidget(QWidget):
    def __init__(self, mwindow):
        self.printLevels = {'D': 0, '>': 0,
                            'I': 1, ':': 1,
                            'W': 2,
                            'F': 3, '!': 4}
        self.printLevel = self.printLevels['I']
        self.clipboard = None
        self.cmdRows = []

        QWidget.__init__(self)
        self.mwindow = mwindow

        self.mainLayout = QVBoxLayout()
        self.scheduler = Scheduler(self)
        self.logLayout = LogLayout(self)

        self.menuBar = self.createMenu()
        self.sequenceTable = Table(self)

        self.mainLayout.addWidget(self.menuBar)
        self.mainLayout.addWidget(self.sequenceTable)
        self.mainLayout.addLayout(self.scheduler)

        self.mainLayout.addLayout(self.logLayout)

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
        return Dialog(self)

    def annotate(self):
        return Annotate(self)

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
        self.mainLayout.insertWidget(1, self.sequenceTable)

        if scrollvalue:
            self.sequenceTable.verticalScrollBar().setScrollValue(value=scrollvalue)

    def sendCommand(self, fullCmd, timeLim=300, callFunc=None):
        callFunc = self.logLayout.logArea.printResponse if callFunc is None else callFunc

        import opscore.actor.keyvar as keyvar

        try:
            [actor, cmdStr] = fullCmd.split(' ', 1)
        except ValueError:
            return

        self.logLayout.logArea.newLine('cmdIn=%s %s' % (actor, cmdStr))
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

        annotate = QAction('Annotate', self)
        annotate.triggered.connect(self.annotate)

        fileMenu.addAction(loadSequence)
        fileMenu.addAction(saveSequence)

        addMenu.addAction(addSequence)

        editMenu.addAction(selectAll)
        editMenu.addAction(clearDone)
        editMenu.addAction(annotate)

        return menubar

    def loadFile(self):
        filepath, fmt = QFileDialog.getOpenFileName(self, 'Open File', '/home/', "(*.yaml)")
        if not filepath:
            return

        try:
            with open(os.path.expandvars(filepath), 'r') as cfgFile:
                cmdRows = yaml.load(cfgFile, Loader=yaml.FullLoader)

        except PermissionError as e:
            self.mwindow.critical(str(e))
            return

        try:
            for i, kwargs in cmdRows.items():
                self.add(CmdRow(self, **kwargs))

        except:
            self.mwindow.critical('yaml file is badly formatted ...')
            return

    def saveFile(self):

        if not self.cmdRows:
            self.mwindow.critical('Your script is empty...')
            return

        seq = dict([(i, cmdRow.info) for i, cmdRow in enumerate(self.cmdRows)])

        try:

            filepath, fmt = QFileDialog.getSaveFileName(self, 'Save File',
                                                        f'/home/script.yaml', "(*.yaml)")
            if filepath:
                with open(os.path.expandvars(filepath), 'w') as savedFile:
                    yaml.dump(seq, savedFile)

        except PermissionError as e:
            self.mwindow.critical(str(e))

    def selectAll(self):
        self.sequenceTable.selectAll()

    def copy(self, cmdRows):
        self.clipboard = [cmdRow.info for cmdRow in cmdRows]

    def paste(self, ind):
        if self.clipboard is None:
            return

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

    def resizeEvent(self, event):
        QWidget.resizeEvent(self, event)
        self.sequenceTable.resizeEvent(event)

    def adjustSize(self):
        QWidget.adjustSize(self)
        self.mwindow.adjustSize()
