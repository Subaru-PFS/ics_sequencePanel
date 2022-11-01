__author__ = 'alefur'

from datetime import datetime as dt
from datetime import timedelta

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QGridLayout, QSpinBox, QProgressBar, QMessageBox
from sequencePanel.widgets import CLabel, Label, PushButton


class SafetyCheck(QMessageBox):
    def __init__(self, **kwargs):
        QMessageBox.__init__(self, **kwargs)
        self.setWindowTitle('Data acquisition scheduler')
        self.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)


class StopMessage(SafetyCheck):
    def __init__(self, **kwargs):
        SafetyCheck.__init__(self, **kwargs)
        self.setIcon(QMessageBox.Critical)
        self.setText('Do you really wish to stop ?')


class AbortMessage(SafetyCheck):
    def __init__(self, **kwargs):
        SafetyCheck.__init__(self, **kwargs)
        self.setIcon(QMessageBox.Critical)
        self.setText('Do you really wish to abort current sequence ?')


class FinishMessage(SafetyCheck):
    def __init__(self, **kwargs):
        SafetyCheck.__init__(self, **kwargs)
        self.setIcon(QMessageBox.Critical)
        self.setText('Do you really wish to finish current sequence ?')


class FinishNowMessage(SafetyCheck):
    def __init__(self, **kwargs):
        SafetyCheck.__init__(self, **kwargs)
        self.setIcon(QMessageBox.Critical)
        self.setText('Do you really wish to finish current sequence now ?')


class StartMessage(SafetyCheck):
    def __init__(self, startdate, **kwargs):
        SafetyCheck.__init__(self, **kwargs)
        self.setIcon(QMessageBox.Information)
        self.setText(f'Do you want to schedule your data at {startdate} ?')


class AbortButton(PushButton):
    def __init__(self):
        PushButton.__init__(self, 'ABORT')
        self.setColor('red')

    def setColor(self, background, color="white"):
        self.setStyleSheet("PushButton {font: 8pt; background-color: %s;color : %s ;}" % (background, color))


class FinishButton(PushButton):
    def __init__(self):
        PushButton.__init__(self, 'FINISH')
        self.setColor('blue')

    def setColor(self, background, color="white"):
        self.setStyleSheet("PushButton {font: 8pt; background-color: %s;color : %s ;}" % (background, color))


class FinishNowButton(PushButton):
    def __init__(self):
        PushButton.__init__(self, 'FINISH NOW')
        self.setColor('orange')

    def setColor(self, background, color="white"):
        self.setStyleSheet("PushButton {font: 8pt; background-color: %s;color : %s ;}" % (background, color))


class DelayBar(QProgressBar):
    def __init__(self, scheduler):
        self.scheduler = scheduler
        QProgressBar.__init__(self)
        self.setStyleSheet("QProgressBar { font: 8pt;}")
        self.setFixedSize(160, 28)

        self.setVisible(False)
        self.progressing = QTimer(scheduler)
        self.progressing.setInterval(500)
        self.progressing.timeout.connect(self.wait)

    @property
    def delta(self):
        return int((dt.now() - self.tstart).total_seconds())

    def start(self, delay):
        self.delay = delay
        self.tstart = dt.now()
        self.setValue(0)
        self.setRange(0, delay)
        self.setFormat("Start : %s \r\n " % self.startDate(delay) + '%p%')
        self.setVisible(True)
        self.progressing.start()

    def startDate(self, delay):
        return (dt.now() + timedelta(seconds=delay)).isoformat()[: -10]

    def stop(self):
        self.progressing.stop()
        self.hide()

    def wait(self):
        if self.delta < self.delay:
            self.setValue(self.delta)
        else:
            self.stop()
            self.scheduler.activate()


class Scheduler(QGridLayout):
    delayCmd = 2

    def __init__(self, panelwidget):
        self.panelwidget = panelwidget
        QGridLayout.__init__(self)
        self.doAbort = False
        self.stateWidget = CLabel('OFF')
        self.startButton = PushButton("START")
        self.stopButton = PushButton("STOP")
        self.finishButton = FinishButton()
        self.finishNowButton = FinishNowButton()
        self.abortButton = AbortButton()

        self.delayBar = DelayBar(self)

        self.delay = QSpinBox()
        self.delay.setValue(0)
        self.delay.setRange(0, 24 * 60 * 10)

        self.startButton.clicked.connect(self.start)
        self.stopButton.clicked.connect(self.stop)
        self.finishButton.clicked.connect(self.finish)
        self.finishNowButton.clicked.connect(self.finishNow)
        self.abortButton.clicked.connect(self.abort)

        self.addWidget(Label("Delay (min)"), 0, 1)
        self.addWidget(self.stateWidget, 1, 0)
        self.addWidget(self.delay, 1, 1)
        self.addWidget(self.delayBar, 0, 2, 1, 2)

        self.addWidget(self.startButton, 1, 2)
        self.addWidget(self.stopButton, 1, 2)
        self.addWidget(self.finishButton, 1, 3)
        self.addWidget(self.finishNowButton, 1, 4)
        self.addWidget(self.abortButton, 1, 5)

        self.setState('off')

    @property
    def validated(self):
        return [cmdRow for cmdRow in self.panelwidget.cmdRows if cmdRow.isValid]

    @property
    def activated(self):
        return [cmdRow for cmdRow in self.panelwidget.cmdRows if cmdRow.isActive]

    def setState(self, state):
        self.state = state
        self.stateWidget.setText(state.upper())

        self.startButton.setVisible(self.state == 'off')
        self.stopButton.setVisible(self.state in ['waiting', 'processing'])

        self.finishButton.setVisible(bool(len(self.activated)))
        self.finishNowButton.setVisible(bool(len(self.activated)))
        self.abortButton.setVisible(bool(len(self.activated)))

    def start(self):
        if self.activated:
            self.activate()
            return

        if not len(self.validated):
            self.panelwidget.mwindow.critical('No valid sequence has been scheduled...')
            return

        delay = self.delay.value() * 60
        delay = Scheduler.delayCmd if not delay else delay

        msgBox = StartMessage(self.delayBar.startDate(delay), parent=self.panelwidget)

        if msgBox.exec() != QMessageBox.Ok:
            return

        self.nextSVP(delay=delay)

    def activate(self):
        if self.activated:
            self.setState('processing')
            return

        try:
            self.validated[0].setActive()
            self.setState('processing')
        except IndexError:
            self.stop(safetyCheck=False)

    def nextSVP(self, delay=None):
        if not len(self.validated) or self.doAbort:
            self.stop(safetyCheck=False)
            self.doAbort = False
            return

        delay = Scheduler.delayCmd if delay is None else delay
        self.setState('waiting')
        self.delayBar.start(delay=delay)

    def stop(self, safetyCheck=True):
        if safetyCheck:
            msgBox = StopMessage(parent=self.panelwidget)
            if msgBox.exec() != QMessageBox.Ok:
                return

        self.setState('off')
        self.delayBar.stop()

    def abort(self):
        if not self.activated:
            self.panelwidget.mwindow.critical('Nothing to abort here...')
            return

        msgBox = AbortMessage(parent=self.panelwidget)
        if msgBox.exec() != QMessageBox.Ok:
            return

        self.panelwidget.sendCommand(fullCmd='iic sps abortExposure', timeLim=10)
        self.doAbort = True

    def finish(self):
        if not self.activated:
            self.panelwidget.mwindow.critical('Nothing to finish here...')
            return

        msgBox = FinishMessage(parent=self.panelwidget)
        if msgBox.exec() != QMessageBox.Ok:
            return

        self.panelwidget.sendCommand(fullCmd='iic sps finishExposure', timeLim=10)
        self.doAbort = True

    def finishNow(self):
        if not self.activated:
            self.panelwidget.mwindow.critical('Nothing to finish here...')
            return

        msgBox = FinishNowMessage(parent=self.panelwidget)
        if msgBox.exec() != QMessageBox.Ok:
            return

        self.panelwidget.sendCommand(fullCmd='iic sps finishExposure now', timeLim=10)
        self.doAbort = True
