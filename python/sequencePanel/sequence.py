__author__ = 'alefur'

from functools import partial

import numpy as np
from PyQt5.QtWidgets import QCheckBox
from sequencePanel.widgets import IconButton, EyeButton


class SubCommand(object):
    def __init__(self, subId, cmdStr, didFail, returnStr):
        self.id = subId
        self.cmdStr = cmdStr
        self.anomalies = ''
        self.returnStr = returnStr

        self.visit = self.decode(returnStr)
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

    def decode(self, returnStr):
        try:
            __, keys = returnStr.split('fileids=')
            visit, __, mask = keys.split(',')
        except ValueError:
            return -1

        return int(visit)


class CmdRow(object):
    color = {"init": ("#FF7D7D", "#000000"), "valid": ("#7DFF7D", "#000000"), "active": ("#4A90D9", "#FFFFFF"),
             "finished": ("#5f9d63", "#FFFFFF"), "failed": ("#9d5f5f", "#FFFFFF")}

    def __init__(self, panelwidget, name, comments, cmdStr, seqtype=''):
        self.status = 'init'
        self.id = -1
        self.panelwidget = panelwidget
        self.seqtype = seqtype
        self.name = name
        self.comments = comments
        self.cmdStr = cmdStr
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
    def fullCmd(self):
        name = f'name="{self.name}"' if self.name else ''
        comments = f'comments="{self.comments}"' if self.comments else ''
        return f'{self.cmdStr} {name} {comments}'.strip()

    @property
    def info(self):
        return dict(name=self.name, comments=self.comments, cmdStr=self.cmdStr)

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
        self.valid.setStyleSheet("QCheckBox {background-color:%s};" % CmdRow.color[self.status][0])

    def setStatus(self, status):
        self.status = status
        self.colorCheckbox()

        self.panelwidget.updateTable()

    def setActive(self):
        self.setStatus(status='active')
        self.valid.setEnabled(False)

        self.panelwidget.sendCommand(fullCmd=self.fullCmd,
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

        self.panelwidget.logLayout.logArea.printResponse(resp=resp)

    def updateInfo(self, reply):

        if 'sps_sequence' in reply.keywords:
            self.setSequence(*reply.keywords['sps_sequence'].values)

        if 'experiment' in reply.keywords:
            self.setExperiment(*reply.keywords['experiment'].values)

        if 'subCommand' in reply.keywords:
            self.updateSubCommand(*reply.keywords['subCommand'].values)

    def terminate(self, code, returnStr):
        self.returnStr = returnStr
        self.setFinished() if code == ':' else self.setFailed()

        self.panelwidget.scheduler.nextSVP()

    def setSequence(self, sequenceId, seqtype, cmdStr, name, comments, *args):

        self.id = int(sequenceId)
        self.seqtype = seqtype
        self.name = name
        self.comments = comments
        self.cmdStr = cmdStr
        self.buttonEye.setEnabled(True)

        self.panelwidget.updateTable()

    def setExperiment(self, dbname, experimentId, seqtype, cmdStr, name, comments):

        self.dbname = dbname
        self.id = int(experimentId)
        self.seqtype = seqtype
        self.name = name
        self.comments = comments
        self.cmdStr = cmdStr
        self.buttonEye.setEnabled(True)

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
        cmdRows = self.panelwidget.cmdRows

        new_ind = cmdRows.index(self) - 1
        new_ind = 0 if new_ind < 0 else new_ind
        cmdRows.remove(self)
        cmdRows.insert(new_ind, self)

        self.panelwidget.updateTable()

    def moveDown(self):
        cmdRows = self.panelwidget.cmdRows

        new_ind = cmdRows.index(self) + 1
        new_ind = len(cmdRows) - 1 if new_ind > len(cmdRows) - 1 else new_ind
        cmdRows.remove(self)
        cmdRows.insert(new_ind, self)

        self.panelwidget.updateTable()

    def remove(self):
        if not self.isActive:
            cmdRows = self.panelwidget.cmdRows
            cmdRows.remove(self)

            self.panelwidget.updateTable()
