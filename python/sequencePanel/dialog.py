__author__ = 'alefur'

from PyQt5.QtWidgets import QGridLayout, QVBoxLayout, QLabel, QDialog, QDialogButtonBox
from sequencePanel.experiment import ExperimentRow
from sequencePanel.widgets import Label, LineEdit, ComboBox


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
        self.cmdStr.setText(self.cmdDescriptor + 'exptime=2.0 duplicate=2 switchOn=hgar,neon switchOff=hgar,neon attenuator=120 cam=r1')


class FlatLayout(ExperimentLayout):
    def __init__(self):
        ExperimentLayout.__init__(self, type='Flats')
        self.cmdDescriptor = 'spsait expose flat '
        self.cmdStr.setText(self.cmdDescriptor + 'exptime=2.0 duplicate=2 switchOff attenuator=120 cam=r1')


class BiasesLayout(ExperimentLayout):
    def __init__(self):
        ExperimentLayout.__init__(self, type='Biases')
        self.cmdDescriptor = 'spsait bias '
        self.cmdStr.setText(self.cmdDescriptor + 'duplicate=3 cam=r1')

class DarksLayout(ExperimentLayout):
    def __init__(self):
        ExperimentLayout.__init__(self, type='Darks')
        self.cmdDescriptor = 'spsait dark '
        self.cmdStr.setText(self.cmdDescriptor + 'exptime=2.0 duplicate=3 cam=r1')

class CalibLayout(ExperimentLayout):
    def __init__(self):
        ExperimentLayout.__init__(self, type='Calib')
        self.cmdDescriptor = 'spsait calib '
        self.cmdStr.setText(self.cmdDescriptor + 'nbias=1 ndarks=1 exptime=2.0 cam=r1')

class SacAlignLayout(ExperimentLayout):
    def __init__(self):
        ExperimentLayout.__init__(self, type='SacAlign')
        self.cmdDescriptor = 'spsait sac align '
        self.cmdStr.setText(self.cmdDescriptor + 'exptime=2.0 focus=5.0 lowBound=-2 upBound=2 nbPosition=4 duplicate=2')


class SlitAlignLayout(ExperimentLayout):
    def __init__(self):
        ExperimentLayout.__init__(self, type='SlitAlign')
        self.cmdDescriptor = 'spsait slit throughfocus '
        self.cmdStr.setText(self.cmdDescriptor + 'exptime=2.0 lowBound=-2 upBound=2 nbPosition=4 duplicate=2')


class DetAlignLayout(ExperimentLayout):
    def __init__(self):
        ExperimentLayout.__init__(self, type='DetAlign')
        self.cmdDescriptor = 'spsait detector throughfocus '
        self.cmdStr.setText(
            self.cmdDescriptor + 'exptime=2.0 cam=r1 startPosition=0,0,40 upBound=290 nbPosition=10 duplicate=2 switchOn=hgar switchOff=hgar')


class DitheredFlatsLayout(ExperimentLayout):
    def __init__(self):
        ExperimentLayout.__init__(self, type='DitheredFlats')
        self.cmdDescriptor = 'spsait dither flat '
        self.cmdStr.setText(
            self.cmdDescriptor + 'exptime=2.0 shift=0.3 nbPosition=10 pixels duplicate=2 switchOff cam=r1')


class DitheredPsfLayout(ExperimentLayout):
    def __init__(self):
        ExperimentLayout.__init__(self, type='DitheredPsf')
        self.cmdDescriptor = 'spsait dither psf '
        self.cmdStr.setText(
            self.cmdDescriptor + 'exptime=2.0 shift=0.5 pixels duplicate=2 switchOn=hgar switchOff=hgar cam=r1')

class DefocusedPsfLayout(ExperimentLayout):
    def __init__(self):
        ExperimentLayout.__init__(self, type='DefocusedPsf')
        self.cmdDescriptor = 'spsait defocus '
        self.cmdStr.setText(
            self.cmdDescriptor + 'exptime=2.0 nbPosition=10 switchOn=hgar switchOff=hgar duplicate=2 cam=r1')

class ImageStabilityLayout(ExperimentLayout):
    def __init__(self):
        ExperimentLayout.__init__(self, type='ImageStability')
        self.cmdDescriptor = 'spsait imstab '
        self.cmdStr.setText(
            self.cmdDescriptor + 'exptime=2.0 nbPosition=10 delay=60 duplicate=2 switchOn=hgar switchOff=hgar cam=r1')

class Dialog(QDialog):
    def __init__(self, panelwidget):
        QDialog.__init__(self, panelwidget)
        self.panelwidget = panelwidget
        self.availableSeq = dict(Command=CommandLayout,
                                 Arcs=ArcLayout,
                                 Flats=FlatLayout,
                                 Biases=BiasesLayout,
                                 Darks=DarksLayout,
                                 SacAlign=SacAlignLayout,
                                 SlitAlign=SlitAlignLayout,
                                 DetAlign=DetAlignLayout,
                                 DitheredFlats=DitheredFlatsLayout,
                                 DitheredPsf=DitheredPsfLayout,
                                 DefocusedPsf=DefocusedPsfLayout,
                                 ImageStability=ImageStabilityLayout,
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
            self.seqLayout.clearLayout()
            self.grid.removeItem(self.seqLayout)

        except Exception as e:
            pass

        obj = self.availableSeq[self.comboType.currentText()]
        self.seqLayout = obj()
        self.grid.addLayout(self.seqLayout, 2, 0, self.seqLayout.rowCount(), self.seqLayout.columnCount())

    def addSequence(self):
        type = self.seqLayout.type.text()
        name = self.seqLayout.name.text()
        comments = self.seqLayout.comments.text()
        cmdDescriptor = self.seqLayout.cmdDescriptor
        cmdStr = self.seqLayout.cmdStr.text()

        experiment = ExperimentRow(self.panelwidget, type=type, name=name, comments=comments,
                                   cmdDescriptor=cmdDescriptor, cmdStr=cmdStr)

        self.panelwidget.addExperiment(experiment=experiment)
