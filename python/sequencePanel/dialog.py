__author__ = 'alefur'

from PyQt5.QtWidgets import QGridLayout, QVBoxLayout, QLabel, QDialog, QDialogButtonBox
from sequencePanel.experiment import ExperimentRow
from sequencePanel.widgets import Label, LineEdit, ComboBox, SpinBox
from spsaitActor.utils.logbook import Logbook


class ExperimentLayout(QGridLayout):
    def __init__(self,
                 type='Experiment',
                 commandParse=('spsait expose', 'arc <exptime>')):

        QGridLayout.__init__(self)
        self.cmdDescriptor = ''
        self.typeLabel = Label('Type')
        self.type = Label(type)

        self.nameLabel = Label('Name')
        self.name = LineEdit('')

        self.commentsLabel = Label('Comments')
        self.comments = LineEdit('')

        self.cmdStrLabel = Label('CmdStr')
        self.cmdStr = LineEdit('')

        self.addWidget(self.typeLabel, 1, 0)
        self.addWidget(self.type, 1, 1)

        self.addWidget(self.nameLabel, 2, 0)
        self.addWidget(self.name, 2, 1)

        self.addWidget(self.commentsLabel, 3, 0)
        self.addWidget(self.comments, 3, 1)

        self.addWidget(self.cmdStrLabel, 4, 0)
        self.addWidget(self.cmdStr, 4, 1)

    def clearLayout(self):
        while self.count():
            item = self.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()


class CommandLayout(ExperimentLayout):
    def __init__(self):
        ExperimentLayout.__init__(self, type='Command')
        self.nameLabel.setDisabled(True)
        self.name.setDisabled(True)
        self.commentsLabel.setDisabled(True)
        self.comments.setDisabled(True)


class ArcLayout(ExperimentLayout):
    def __init__(self):
        ExperimentLayout.__init__(self, type='Arcs')
        self.cmdDescriptor = 'spsait expose arc '
        self.cmdStr.setText(
            self.cmdDescriptor + 'exptime=15.0 duplicate=5 switchOn=hgar switchOff=hgar attenuator=120 cam=r1')


class FlatLayout(ExperimentLayout):
    def __init__(self):
        ExperimentLayout.__init__(self, type='Flats')
        self.cmdDescriptor = 'spsait expose flat '
        self.cmdStr.setText(self.cmdDescriptor + 'exptime=15.0 duplicate=2 switchOff attenuator=240 cam=r1')


class BiasesLayout(ExperimentLayout):
    def __init__(self):
        ExperimentLayout.__init__(self, type='Biases')
        self.cmdDescriptor = 'spsait bias '
        self.cmdStr.setText(self.cmdDescriptor + 'duplicate=15 cam=r1')


class DarksLayout(ExperimentLayout):
    def __init__(self):
        ExperimentLayout.__init__(self, type='Darks')
        self.cmdDescriptor = 'spsait dark '
        self.cmdStr.setText(self.cmdDescriptor + 'exptime=60.0 duplicate=5 cam=r1')


class SlitAlignLayout(ExperimentLayout):
    def __init__(self):
        ExperimentLayout.__init__(self, type='SlitAlign')
        self.cmdDescriptor = 'spsait slit align '
        self.cmdStr.setText(self.cmdDescriptor + 'exptime=2.0 position=-2,2,10 duplicate=2')


class SlitTFLayout(ExperimentLayout):
    def __init__(self):
        ExperimentLayout.__init__(self, type='SlitTF')
        self.cmdDescriptor = 'spsait slit throughfocus '
        self.cmdStr.setText(self.cmdDescriptor + 'exptime=15.0 position=-2,2,10 duplicate=2 cam=r1')


class DetAlignLayout(ExperimentLayout):
    def __init__(self):
        ExperimentLayout.__init__(self, type='DetAlign')
        self.cmdDescriptor = 'spsait detector throughfocus '
        self.cmdStr.setText(
            self.cmdDescriptor + 'exptime=2.0 cam=r1 position=10,300,20 tilt=0,0,40 duplicate=2 switchOn=hgar switchOff=hgar')


class DitheredFlatsLayout(ExperimentLayout):
    def __init__(self):
        ExperimentLayout.__init__(self, type='DitheredFlats')
        self.cmdDescriptor = 'spsait dither flat '
        self.cmdStr.setText(
            self.cmdDescriptor + 'exptime=15.0 pixels=0.3 nbPosition=20 duplicate=3 switchOff cam=r1')


class DitheredPsfLayout(ExperimentLayout):
    def __init__(self):
        ExperimentLayout.__init__(self, type='DitheredPsf')
        self.cmdDescriptor = 'spsait dither psf '
        self.cmdStr.setText(
            self.cmdDescriptor + 'exptime=15.0 pixels=0.5 duplicate=2 switchOn=hgar cam=r1')


class DefocusedPsfLayout(ExperimentLayout):
    def __init__(self):
        ExperimentLayout.__init__(self, type='DefocusedPsf')
        self.cmdDescriptor = 'spsait defocus '
        self.cmdStr.setText(
            self.cmdDescriptor + 'exptime=15.0 attenuator=200 position=-5,5,20 switchOn=hgar switchOff=hgar duplicate=2 cam=r1')


class ImageStabilityLayout(ExperimentLayout):
    def __init__(self):
        ExperimentLayout.__init__(self, type='ImageStability')
        self.cmdDescriptor = 'spsait imstab '
        self.cmdStr.setText(
            self.cmdDescriptor + 'exptime=2.0 duration=24 delay=0.5 duplicate=2 switchOn=hgar switchOff=hgar cam=r1')


class PreviousExperimentLayout(ExperimentLayout):
    def __init__(self):
        ExperimentLayout.__init__(self, type='previous')

        self.databaseLabel = Label('Database')
        self.database = LineEdit('experimentLog')

        self.experimentIdLabel = Label('experimentId')
        self.experimentId = SpinBox()
        self.experimentId.setMinimum(1)
        self.experimentId.valueChanged.connect(self.loadPreviousCmdStr)
        self.experimentId.setValue(Logbook.lastExperimentId(self.database.text()))

        for row in [2, 3, 4]:
            self.removeItem(self.itemAtPosition(row, 0))
            self.removeItem(self.itemAtPosition(row, 1))

        self.addWidget(self.databaseLabel, 2, 0)
        self.addWidget(self.database, 2, 1)

        self.addWidget(self.experimentIdLabel, 3, 0)
        self.addWidget(self.experimentId, 3, 1)

        self.addWidget(self.nameLabel, 4, 0)
        self.addWidget(self.name, 4, 1)

        self.addWidget(self.commentsLabel, 5, 0)
        self.addWidget(self.comments, 5, 1)

        self.addWidget(self.cmdStrLabel, 6, 0)
        self.addWidget(self.cmdStr, 6, 1)

    def loadPreviousCmdStr(self, experimentId):
        try:
            name, comments, cmdStr = Logbook.buildCmdStr(self.database.text(), experimentId)
            self.name.setEnabled(True)
            self.comments.setEnabled(True)
            self.cmdStr.setEnabled(True)
            self.name.setText(name)
            self.comments.setText(comments)
            self.cmdStr.setText(cmdStr)

        except TypeError:
            self.name.setDisabled(True)
            self.comments.setDisabled(True)
            self.cmdStr.setDisabled(True)


class SacAlignLayout(ExperimentLayout):
    def __init__(self):
        ExperimentLayout.__init__(self, type='SacAlign')
        self.cmdDescriptor = 'spsait sac align '
        self.cmdStr.setText(self.cmdDescriptor + 'exptime=2.0 position=-300,500,10 focus=5.0  duplicate=2')


class SacExposeLayout(ExperimentLayout):
    def __init__(self):
        ExperimentLayout.__init__(self, type='SacExpose')
        self.cmdDescriptor = 'spsait sac expose '
        self.cmdStr.setText(self.cmdDescriptor + 'exptime=2.0 duplicate=2')


class SacBackgroundLayout(ExperimentLayout):
    def __init__(self):
        ExperimentLayout.__init__(self, type='SacBackground')
        self.cmdDescriptor = 'spsait sac background '
        self.cmdStr.setText(self.cmdDescriptor + 'exptime=2.0 duplicate=2')


class Dialog(QDialog):
    def __init__(self, panelwidget):
        QDialog.__init__(self, panelwidget)
        self.panelwidget = panelwidget
        self.availableSeq = dict(Command=CommandLayout,
                                 Arcs=ArcLayout,
                                 Flats=FlatLayout,
                                 Biases=BiasesLayout,
                                 Darks=DarksLayout,
                                 SlitAlign=SlitAlignLayout,
                                 SlitTF=SlitTFLayout,
                                 DetAlign=DetAlignLayout,
                                 DitheredFlats=DitheredFlatsLayout,
                                 DitheredPsf=DitheredPsfLayout,
                                 DefocusedPsf=DefocusedPsfLayout,
                                 ImageStability=ImageStabilityLayout,
                                 Previous=PreviousExperimentLayout,
                                 SacAlign=SacAlignLayout,
                                 SacExpose=SacExposeLayout,
                                 SacBackground=SacBackgroundLayout,

                                 )

        vbox = QVBoxLayout()
        self.grid = QGridLayout()
        self.grid.setSpacing(10)

        self.comboLabel = QLabel('Sequence type')

        self.comboType = ComboBox()
        self.comboType.addItems(list(self.availableSeq.keys()))
        self.comboType.currentIndexChanged.connect(self.showRelevantWidgets)
        self.comboType.setCurrentIndex(1)

        self.grid.addWidget(self.comboLabel, 1, 0)
        self.grid.addWidget(self.comboType, 1, 1)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Apply | QDialogButtonBox.Close)
        buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self.addSequence)
        buttonBox.button(QDialogButtonBox.Close).clicked.connect(self.close)

        self.setLayout(vbox)

        vbox.addLayout(self.grid)
        vbox.addWidget(buttonBox)

        self.setWindowTitle('Add Sequence')
        self.setVisible(True)
        self.setMinimumWidth(400)

    def showRelevantWidgets(self):
        try:
            name = self.seqLayout.name.text()
            comments = self.seqLayout.comments.text()
            self.seqLayout.clearLayout()
            self.grid.removeItem(self.seqLayout)
            self.adjustSize()

        except Exception as e:
            name = ''
            comments = ''

        obj = self.availableSeq[self.comboType.currentText()]
        self.seqLayout = obj()
        self.grid.addLayout(self.seqLayout, 2, 0, self.seqLayout.rowCount(), self.seqLayout.columnCount())
        self.adjustSize()
        self.seqLayout.name.setText(name)
        self.seqLayout.comments.setText(comments)

    def addSequence(self):
        type = self.seqLayout.type.text()
        name = self.seqLayout.name.text()
        comments = self.seqLayout.comments.text()
        cmdDescriptor = self.seqLayout.cmdDescriptor
        cmdStr = self.seqLayout.cmdStr.text()

        experiment = ExperimentRow(self.panelwidget, type=type, name=name, comments=comments,
                                   cmdDescriptor=cmdDescriptor, cmdStr=cmdStr)

        self.panelwidget.addExperiment(experiment=experiment)
