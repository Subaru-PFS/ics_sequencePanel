__author__ = 'alefur'
import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QDialog, QDialogButtonBox, QTableWidget, QTableWidgetItem, QMessageBox
from opdb import utils, opdb
from sequencePanel.dialog import Previous
from sequencePanel.utils import visitsFromSet, spsExposure


class DataFlag(QTableWidgetItem):
    values = ['0', '1', 'OK', 'BAD']
    flags = dict(OK=0, BAD=1)
    revFlags = dict([(v,k) for k,v in flags.items()])

    def __init__(self, dataFlag):
        try:
            dataFlag = DataFlag.revFlags[dataFlag]
        except:
            dataFlag = ""

        self.current = dataFlag
        QTableWidgetItem.__init__(self, dataFlag)
        self.setTextAlignment(Qt.AlignCenter)
        if dataFlag:
            self.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

    def valueChanged(self):

        current = self.text().upper().strip()
        if current and current not in DataFlag.values:
            self.tableWidget().panelWidget.mwindow.critical(f'{current} is not an existing flag :{DataFlag.values}')
        else:
            self.current = current
        self.setText(self.current)

    def value(self):
        try:
            value = int(self.text())
        except ValueError:
            value = DataFlag.flags[self.text()]

        return value


class Notes(QTableWidgetItem):
    def __init__(self, notes, visit, camId, dataFlag):
        self.locked = False
        self.visit = int(visit)
        self.camId = int(camId)
        self.dataFlag = dataFlag
        QTableWidgetItem.__init__(self, notes)
        self.setTextAlignment(Qt.AlignCenter)

        if notes:
            self.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.locked = True

    def valueChanged(self):
        if self.text() and not self.dataFlag.text():
            self.dataFlag.setText('BAD')

    def build(self):
        if not self.text() or self.locked:
            return None

        return dict(pfs_visit_id=self.visit, sps_camera_id=self.camId, data_flag=self.dataFlag.value(),
                    notes=self.text())


class LockedItem(QTableWidgetItem):

    def __init__(self, value):
        QTableWidgetItem.__init__(self, value)
        self.setTextAlignment(Qt.AlignCenter)
        self.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

    def valueChanged(self):
        pass


class SeqDescription(Previous):
    def __init__(self, annotate):
        self.annotate = annotate
        Previous.__init__(self)
        self.name.setReadOnly(True)
        self.comments.setReadOnly(True)
        self.cmdStr.setReadOnly(True)

    def load(self):
        Previous.load(self)
        self.annotate.load(self.visitSetId.value())


class Exposures(QTableWidget):
    colnames = ['visit', 'expType', 'expTime', 'cam', 'dataFlag', 'notes']

    def __init__(self, panelWidget):
        self.panelWidget = panelWidget
        self.remainingWidth = None
        QTableWidget.__init__(self, 0, len(Exposures.colnames))

        self.setHorizontalHeaderLabels(Exposures.colnames)
        self.verticalHeader().setDefaultSectionSize(6)
        self.verticalHeader().hide()
        self.cellChanged.connect(self.userCellChanged)

    def setExposures(self, expList):
        self.clearContents()
        self.setRowCount(len(expList))

        for row, exp in expList.iterrows():
            df = utils.fetch_query(opdb.OpDB.url,
                                   f'select data_flag, notes from sps_annotation where pfs_visit_id={exp.visit} and sps_camera_id={exp.camId}')
            dataFlag, notes = ('', '') if not len(df) else df.loc[0].values
            dataFlag = DataFlag(dataFlag)
            expTime = round(float(exp.exptime), 3)
            self.setItem(row, 0, LockedItem(exp.visit))
            self.setItem(row, 1, LockedItem(exp.exptype))
            self.setItem(row, 2, LockedItem(str(expTime)))
            self.setItem(row, 3, LockedItem(f'{exp.arm}{exp.specNum}'))
            self.setItem(row, 4, dataFlag)
            self.setItem(row, 5, Notes(notes, visit=exp.visit, camId=exp.camId, dataFlag=dataFlag))

        self.resizeColumnsToContents()
        self.resizeRowsToContents()

    def calcWidth(self, event):
        if event is None:
            return self.remainingWidth

        return event.size().width() - sum([self.columnWidth(j) for j in range(5)])

    def resizeEvent(self, event):
        if event is None and self.remainingWidth is None:
            return

        remainingWidth = self.calcWidth(event)
        self.remainingWidth = remainingWidth
        self.setColumnWidth(5, remainingWidth)

    def userCellChanged(self, row, column):
        self.item(row, column).valueChanged()

    def gather(self):
        notes = [self.item(row, 5).build() for row in range(self.rowCount())]
        return list(filter(None, notes))


class SafetyCheck(QMessageBox):
    def __init__(self, insertStatement, **kwargs):
        QMessageBox.__init__(self, **kwargs)
        self.setWindowTitle('Confirm annotation ?')
        self.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

        self.setIcon(QMessageBox.Information)
        self.setText('\n'.join([str(d) for d in insertStatement]))


class Annotate(QDialog):
    def __init__(self, panelwidget):
        QDialog.__init__(self, panelwidget)
        self.panelwidget = panelwidget

        vbox = QVBoxLayout()
        self.expList = Exposures(panelwidget)
        self.grid = SeqDescription(self)
        self.grid.setSpacing(2)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Apply | QDialogButtonBox.Close)
        buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self.apply)
        buttonBox.button(QDialogButtonBox.Close).clicked.connect(self.close)

        self.setLayout(vbox)

        vbox.addLayout(self.grid)
        vbox.addWidget(self.expList)
        vbox.addWidget(buttonBox)

        self.setWindowTitle('Annotate')
        self.setVisible(True)
        self.setMinimumWidth(400)

    def apply(self):
        notes = self.expList.gather()
        if not notes:
            return
        msgBox = SafetyCheck(notes)
        if msgBox.exec() != QMessageBox.Ok:
            return

        for kwargs in notes:
            try:
                utils.insert(opdb.OpDB.url, 'sps_annotation',pd.DataFrame(kwargs, index=[0]))
            except Exception as e:
                self.panelwidget.mwindow.critical(str(e))

    def resizeEvent(self, event):
        QDialog.resizeEvent(self, event)
        self.expList.resizeEvent(event)

    def load(self, visit_set_id):
        visits = visitsFromSet(visit_set_id)
        expList = spsExposure(visits)
        self.expList.setExposures(expList)
        self.expList.resizeEvent(None)
