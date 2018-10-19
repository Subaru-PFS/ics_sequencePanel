__author__ = 'alefur'

from functools import partial

import numpy as np
from PyQt5.QtWidgets import QCheckBox
from opscore.utility.qstr import qstr
from sequencePanel.widgets import IconButton, EyeButton


class SubCommand(object):
    def __init__(self, id, cmdStr):
        self.id = id
        self.cmdStr = cmdStr
        self.visits = []

        self.anomalies = ''
        self.status = 'valid'
        if id == 0:
            self.setActive()

    @property
    def isFinished(self):
        return self.status == 'finished'

    @property
    def isActive(self):
        return self.status == 'active'

    @property
    def visitStart(self):
        if not self.visits:
            return -1

        return min(self.visits)

    @property
    def visitEnd(self):
        if not self.visits:
            return -1

        return max(self.visits)

    def setFinished(self):
        self.status = 'finished'

    def setFailed(self):
        self.status = 'failed'

    def setActive(self):
        self.status = 'active'

    def addVisits(self, newVisits):
        newVisits = [int(visit) for visit in newVisits]
        self.visits.extend(newVisits)


class ExperimentRow(object):
    color = {"init": ("#FF7D7D", "#000000"), "valid": ("#7DFF7D", "#000000"), "active": ("#4A90D9", "#FFFFFF"),
             "finished": ("#5f9d63", "#FFFFFF"), "failed": ("#9d5f5f", "#FFFFFF")}

    def __init__(self, panelwidget, type, name, comments, cmdDescriptor, cmdStr):
        self.status = 'init'
        self.id = -1
        self.panelwidget = panelwidget
        self.type = type
        self.name = name
        self.comments = comments
        self.cmdDescriptor = cmdDescriptor
        self.cmdStr = cmdStr
        self.anomalies = ''
        self.subcommands = []
        self.returnStr = ''

        self.valid = QCheckBox()
        self.valid.stateChanged.connect(self.setValid)
        self.colorCheckbox()

        self.buttonMoveUp = IconButton(iconFile='arrow_up2.png')
        self.buttonMoveUp.clicked.connect(self.moveUp)

        self.buttonMoveDown = IconButton(iconFile='arrow_down2.png')
        self.buttonMoveDown.clicked.connect(self.moveDown)

        self.buttonDelete = IconButton(iconFile='delete.png')
        self.buttonDelete.clicked.connect(self.remove)

        self.buttonEye = EyeButton()
        self.buttonEye.clicked.connect(partial(self.showSubcommands))

    @property
    def kwargs(self):
        return dict(type=self.type, name=self.name, comments=self.comments, cmdDescriptor=self.cmdDescriptor,
                    cmdStr=self.cmdStr)

    @property
    def isValid(self):
        return self.status == 'valid'

    @property
    def isActive(self):
        return self.status == 'active'

    @property
    def showSub(self):
        return self.buttonEye.state

    @property
    def nbRows(self):
        nbRows = len(self.subcommands) if (self.showSub and self.subcommands) else 2
        nbRows = 2 if nbRows < 2 else nbRows
        return nbRows

    @property
    def height(self):
        isActive = [subcommand.isActive for subcommand in self.subcommands]
        height = (np.argmax(isActive) + 0.5) if (self.showSub and isActive) else 1
        return height

    @property
    def visitStart(self):
        visits = [subcommand.visitStart for subcommand in self.subcommands if subcommand.visitStart != -1]
        if not visits:
            return -1

        return min(visits)

    @property
    def visitEnd(self):
        visits = [subcommand.visitEnd for subcommand in self.subcommands if subcommand.visitEnd != -1]
        if not visits:
            return -1

        return max(visits)

    @property
    def registered(self):
        return not self.id == -1

    def colorCheckbox(self):
        self.valid.setStyleSheet("QCheckBox {background-color:%s};" % ExperimentRow.color[self.status][0])

    def setStatus(self, status):
        self.status = status
        self.colorCheckbox()

        self.panelwidget.updateTable()

    def setActive(self):
        self.setStatus(status='active')

        name = 'name="%s"' % self.name.replace('"', "") if self.name else ''
        comments = 'comments="%s"' % self.comments.replace('"', "") if self.comments else ''

        self.panelwidget.sendCommand(fullCmd='%s %s %s' % (self.cmdStr, name, comments),
                                     timeLim=7 * 24 * 3600,
                                     callFunc=self.handleResult)

    def setFinished(self):
        self.valid.setEnabled(False)
        self.setStatus(status='finished')

    def setFailed(self):
        self.valid.setEnabled(False)
        self.cleanupSubCommand()
        self.setStatus(status='failed')

    def setValid(self, state):
        status = "valid" if state == 2 else "init"
        self.setStatus(status=status)

    def showSubcommands(self, bool=None):
        state = not self.buttonEye.state if bool is None else bool
        self.buttonEye.setState(state=state)
        self.panelwidget.updateTable()

    def handleResult(self, resp):
        reply = resp.replyList[-1]
        returnStr = reply.keywords.canonical(delimiter=';')
        code = resp.lastCode

        if code in [':', 'F']:
            self.terminate(code=code, returnStr=qstr(returnStr))
        else:
            self.updateInfo(reply=reply)

        self.panelwidget.printResponse(resp=resp)

    def updateInfo(self, reply):

        if 'newExperiment' in reply.keywords:
            self.setExperiment(*reply.keywords['newExperiment'].values)

        if 'subCommand' in reply.keywords:
            self.updateSubCommand(*reply.keywords['subCommand'].values)

    def terminate(self, code, returnStr):
        self.setFinished() if code == ':' else self.setFailed()
        self.returnStr = returnStr
        self.showSubcommands(bool=False)

        self.panelwidget.sequencer.nextPlease()

    def setExperiment(self, experimentId, exptype, name, comments, cmdList):

        self.id = int(experimentId)
        self.type = exptype.capitalize()
        self.name = name
        self.comments = comments
        self.subcommands = [SubCommand(id=i, cmdStr=cmdStr) for i, cmdStr in enumerate(cmdList.split(';'))]
        self.buttonEye.setEnabled(True)
        self.showSubcommands(bool=True)

        self.panelwidget.updateTable()

    def updateSubCommand(self, id, didFail, returnStr=''):
        id = int(id)
        subcommand = self.subcommands[id]

        if int(didFail):
            subcommand.setFailed()
            subcommand.anomalies = returnStr
        else:
            if returnStr:
                try:
                    subcommand.addVisits(newVisits=returnStr.split(';'))
                except:
                    pass

            subcommand.setFinished()

        try:
            self.subcommands[id + 1].setActive()
        except IndexError:
            pass

        self.panelwidget.updateTable()

    def cleanupSubCommand(self):
        for subcommand in self.subcommands:
            if not subcommand.isFinished:
                subcommand.setFailed()

    def moveUp(self):
        experiments = self.panelwidget.experiments

        new_ind = experiments.index(self) - 1
        new_ind = 0 if new_ind < 0 else new_ind
        experiments.remove(self)
        experiments.insert(new_ind, self)

        self.panelwidget.updateTable()

    def moveDown(self):
        experiments = self.panelwidget.experiments

        new_ind = experiments.index(self) + 1
        new_ind = len(experiments) - 1 if new_ind > len(experiments) - 1 else new_ind
        experiments.remove(self)
        experiments.insert(new_ind, self)

        self.panelwidget.updateTable()

    def remove(self):
        if not self.isActive:
            experiments = self.panelwidget.experiments
            experiments.remove(self)

            self.panelwidget.updateTable()
