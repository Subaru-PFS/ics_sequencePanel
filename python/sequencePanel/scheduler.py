__author__ = 'alefur'

from datetime import datetime as dt
from datetime import timedelta

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QGridLayout, QPushButton, QSpinBox, QProgressBar
from sequencePanel.widgets import CLabel, Label


class AbortButton(QPushButton):
    def __init__(self):
        QPushButton.__init__(self, 'ABORT')
        self.setColor('red')

    def setColor(self, background, color="white"):
        self.setStyleSheet("QPushButton {font: 9pt; background-color: %s;color : %s ;}" % (background, color))

class DelayBar(QProgressBar):
    def __init__(self, panelwidget):
        self.panelwidget = panelwidget
        QProgressBar.__init__(self)
        self.setStyleSheet("QProgressBar { font: 8pt;}")
        self.setVisible(False)
        self.progressing = QTimer(panelwidget)
        self.progressing.setInterval(500)
        self.progressing.timeout.connect(self.waitInProgress)

    @property
    def scheduler(self):
        return self.panelwidget.scheduler

    @property
    def delta(self):
        return (dt.now() - self.tstart).total_seconds()

    def start(self, delay):
        self.tstart = dt.now()
        self.delay = delay

        self.setValue(0)
        self.setRange(0, delay)
        self.setFormat(
            "Start : %s \r\n " % ((self.tstart + timedelta(seconds=delay)).isoformat())[:-10] + '%p%')
        self.setVisible(True)
        self.progressing.start()

    def stop(self):
        self.progressing.stop()
        self.hide()

    def waitInProgress(self):
        if not self.scheduler.onGoing:
            self.stop()
        else:
            if self.delta < self.delay:
                self.setValue(self.delta)
            else:
                self.stop()
                self.scheduler.activateSequence()


class Scheduler(QGridLayout):
    delayCmd = 2
    def __init__(self, panelwidget):
        self.panelwidget = panelwidget
        QGridLayout.__init__(self)
        self.status = CLabel('OFF')
        self.startButton = QPushButton("START")
        self.stopButton = QPushButton("STOP")
        self.abortButton = AbortButton()

        self.delayBar = DelayBar(panelwidget=panelwidget)
        self.delayBar.setFixedSize(160, 28)

        self.delay = QSpinBox()
        self.delay.setValue(0)
        self.delay.setRange(0, 24 * 60 * 10)

        self.startButton.clicked.connect(self.startSequence)
        self.stopButton.clicked.connect(self.stopSequence)
        self.abortButton.clicked.connect(self.abortSequence)

        self.addWidget(Label("Delay (min)"), 0, 1)
        self.addWidget(self.status, 1, 0)
        self.addWidget(self.delay, 1, 1)
        self.addWidget(self.delayBar, 0, 2, 1, 2)

        self.addWidget(self.startButton, 1, 2)
        self.addWidget(self.stopButton, 1, 2)
        self.addWidget(self.abortButton, 1, 3)

        self.stopButton.setVisible(False)

    @property
    def onGoing(self):
        return self.stopButton.isVisible()

    @property
    def validated(self):
        return [cmdRow for cmdRow in self.panelwidget.cmdRows if cmdRow.isValid]

    def startSequence(self):
        self.startButton.setVisible(False)
        self.stopButton.setVisible(True)

        delay = self.delay.value() * 60
        delay = Scheduler.delayCmd if not delay else delay

        self.startingSoon(delay=delay)

    def startingSoon(self, delay):
        if len(self.validated):
            self.status.setText('WAITING')
            self.delayBar.start(delay=delay)
        else:
            self.stopSequence()

    def activateSequence(self):
        isActive = True in [cmdRow.isActive for cmdRow in self.validated]
        self.status.setText('PROCESSING')

        for cmdRow in self.validated:
            if not isActive:
                cmdRow.setActive()
                isActive = True
                break

        if not isActive:
            self.stopSequence()

    def stopSequence(self):
        self.status.setText('OFF')
        self.startButton.setVisible(True)
        self.stopButton.setVisible(False)

    def nextPlease(self):
        if self.onGoing:
            self.startingSoon(delay=Scheduler.delayCmd)

    def abortSequence(self):
        self.panelwidget.sendCommand(fullCmd='spsait abort', timeLim=5)
        self.stopSequence()