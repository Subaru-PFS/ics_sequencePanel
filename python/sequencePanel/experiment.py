__author__ = 'alefur'

from functools import partial

import numpy as np
from PyQt5.QtWidgets import QCheckBox
from opscore.utility.qstr import qstr
from sequencePanel.widgets import IconButton, EyeButton


class SubCommand(object):
    def __init__(self, subId, cmdStr, didFail, returnStr):
        self.id = subId
        self.cmdStr = cmdStr
        self.anomalies = ''
        self.returnStr = returnStr

        self.visit = self.setVisit(returnStr)
        self.setStatus(int(didFail))

    @property
    def isActive(self):
        return self.status == 'active'

    @property
    def isValid(self):
        return self.status == 'valid'

    @property
    def visitStart(self):
        return self.visit

    @property
    def visitEnd(self):
        return self.visit

    def setActive(self):
        self.status = 'active'

    def setStatus(self, didFail):
        if didFail == -1:
            self.status = 'valid'
        elif didFail == 0:
            self.status = 'finished'
        elif didFail == 1:
            self.status = 'failed'

    def setVisit(self, returnStr):
        try:
            visit = int(returnStr.replace("'", "").split('visit=')[1])
            self.returnStr = ''
        except IndexError:
            visit = -1

        return visit


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
        self.cmds = dict()
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
    def subcommands(self):
        return [self.cmds[k] for k in sorted(self.cmds.keys())]

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
    def visits(self):
        return [subcommand.visit for subcommand in self.subcommands if subcommand.visit != -1]

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

    @property
    def registered(self):
        return self.status in ['finished', 'failed'] and self.visits

    def colorCheckbox(self):
        self.valid.setStyleSheet("QCheckBox {background-color:%s};" % ExperimentRow.color[self.status][0])

    def setStatus(self, status):
        self.status = status
        self.colorCheckbox()

        self.panelwidget.updateTable()

    def setActive(self):
        self.setStatus(status='active')
        self.valid.setEnabled(False)

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
        self.setStatus(status='failed')

    def setValid(self, state):
        status = "valid" if state == 2 else "init"
        self.setStatus(status=status)

    def showSubcommands(self, *args, bool=None):
        state = not self.buttonEye.state if bool is None else bool

        self.buttonEye.setState(state=state)
        self.panelwidget.updateTable()

    def handleResult(self, resp):
        reply = resp.replyList[-1]
        returnStr = reply.keywords.canonical(delimiter=';')
        code = resp.lastCode

        if code in [':', 'F']:
            self.terminate(code=code, returnStr=returnStr)
        else:
            self.updateInfo(reply=reply)

        self.panelwidget.printResponse(resp=resp)

    def updateInfo(self, reply):
        if 'experiment' in reply.keywords:
            self.setExperiment(*reply.keywords['experiment'].values)

        if 'subCommand' in reply.keywords:
            self.updateSubCommand(*reply.keywords['subCommand'].values)

    def terminate(self, code, returnStr):
        self.returnStr = returnStr
        self.setFinished() if code == ':' else self.setFailed()
        # self.showSubcommands(bool=False)

        self.panelwidget.sequencer.nextPlease()

    def setExperiment(self, dbname, experimentId, exptype, cmdStr, name, comments):

        self.dbname = dbname
        self.id = int(experimentId)
        self.type = exptype
        self.name = name
        self.comments = comments
        self.buttonEye.setEnabled(True)
        # self.showSubcommands(bool=True)

        self.panelwidget.updateTable()

    def updateSubCommand(self, expId, subId, *args):
        subId = int(subId)
        self.cmds[subId] = SubCommand(subId, *args)

        actives = [subcommand for subcommand in self.subcommands if subcommand.isActive]
        valids = [subcommand for subcommand in self.subcommands if subcommand.isValid]

        if actives:
            return

        if valids:
            valids[0].setActive()

        self.panelwidget.updateTable()

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
