__author__ = 'alefur'

from PyQt5.QtWidgets import QGridLayout, QVBoxLayout, QDialog, QDialogButtonBox, QGroupBox
from ics.utils.opdb import opDB
from sequencePanel.sequence import CmdRow
from sequencePanel.utils import stripQuotes, stripField
from sequencePanel.widgets import Label, LineEdit, ComboBox, SpinBox

dcbArcLamps = ['argon', 'neon', 'krypton', 'hgar']


class CmdStr(LineEdit):
    def __init__(self, sequence, *args, **kwargs):
        LineEdit.__init__(self, *args, **kwargs)
        self.sequence = sequence

    def build(self, text=None):
        fields = list(filter(None, [field.build() for field in self.sequence.fields]))
        cmdStr = ' '.join([self.sequence.cmdHead] + fields)
        self.setText(cmdStr)


class EditableValue(LineEdit):
    def __init__(self, sequence, key, *args, **kwargs):
        LineEdit.__init__(self, *args, **kwargs)
        self.key = key
        self.textChanged.connect(sequence.cmdStr.build)

    def build(self):
        text = self.text().strip()
        if text:
            if text == 'True':
                return self.key
            elif text == 'False':
                return
            else:
                return f'{self.key}={text}'


class ExposureTime(QGroupBox):
    def __init__(self, sequence, lamps=None):
        lamps = [] if lamps is None else lamps
        QGroupBox.__init__(self)
        self.setTitle('Exposure Time')
        self.grid = QGridLayout()
        self.grid.setSpacing(2)
        self.exptime = EditableValue(sequence, 'exptime', '15.0')
        self.fields = [self.exptime]
        self.grid.addWidget(Label('exptime(shutter driven)'), 0, 0)
        self.grid.addWidget(self.exptime, 0, 1)

        for i, key in enumerate(lamps):
            label, editableValue = Label(key), EditableValue(sequence, key, '')
            self.fields.append(editableValue)
            self.grid.addWidget(label, i + 1, 0)
            self.grid.addWidget(editableValue, i + 1, 1)

        self.setLayout(self.grid)


class OptionalArgs(QGroupBox):
    def __init__(self, sequence, options):
        QGroupBox.__init__(self)
        self.setTitle('Optional Arguments')
        self.grid = QGridLayout()
        self.grid.setSpacing(2)
        self.fields = []

        for i, key in enumerate(options):
            label, editableValue = Label(key), EditableValue(sequence, key, '')
            self.fields.append(editableValue)
            self.grid.addWidget(label, i, 0)
            self.grid.addWidget(editableValue, i, 1)

        self.setLayout(self.grid)


class SequenceLayout(QGridLayout):
    def __init__(self, seqtype, cmdHead, lampExptime=None, options=None, **kwargs):
        self.seqtype = seqtype
        self.cmdHead = cmdHead
        QGridLayout.__init__(self)

        self.addWidget(Label('name'), 0, 0)
        self.addWidget(Label('comments'), 1, 0)

        self.cmdStr = CmdStr(self)
        self.name = EditableValue(self, 'name', '')
        self.comments = EditableValue(self, 'comments', '')

        self.fields = []

        self.addWidget(self.name, 0, 1)
        self.addWidget(self.comments, 1, 1)

        if lampExptime is not None:
            exptime = ExposureTime(self, lamps=lampExptime)
            self.fields.extend(exptime.fields)
            self.addWidget(exptime, self.rowCount(), 0, exptime.grid.rowCount(), 2)

        for i, (key, value) in enumerate(kwargs.items()):
            nRows = self.rowCount()
            label, editableValue = Label(key), EditableValue(self, key, str(value))
            self.fields.append(editableValue)
            self.addWidget(label, nRows + i, 0)
            self.addWidget(editableValue, nRows + i, 1)

        nRows = self.rowCount()
        self.addWidget(Label('cmdStr'), nRows, 0)
        self.addWidget(self.cmdStr, nRows, 1)

        if options is not None:
            options = OptionalArgs(self, options)
            self.fields.extend(options.fields)
            self.addWidget(options, self.rowCount(), 0, options.grid.rowCount(), 2)

        self.cmdStr.build()

    def clearLayout(self):
        while self.count():
            item = self.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()


class MasterBiases(SequenceLayout):
    def __init__(self):
        SequenceLayout.__init__(self, 'masterBiases', 'iic masterBiases', duplicate=15, options=['cam'])


class MasterDarks(SequenceLayout):
    def __init__(self):
        SequenceLayout.__init__(self, 'masterDarks', 'iic masterDarks', exptime=300, duplicate=15, options=['cam'])


class DitheredFlats(SequenceLayout):
    def __init__(self):
        SequenceLayout.__init__(self, 'ditheredFlats', 'iic ditheredFlats', pixelRange="-6,6,0.3",
                                options=['exptime', 'halogen', 'duplicate', 'cam', 'warmingTime', 'switchOff'])

        for field in self.fields:
            if field.key == 'switchOff':
                field.setText('False')


class ScienceObject(SequenceLayout):
    def __init__(self):
        SequenceLayout.__init__(self, 'scienceObject', 'iic scienceObject', exptime=15,
                                options=['duplicate', 'cam'])


class ScienceArc(SequenceLayout):
    def __init__(self):
        SequenceLayout.__init__(self, 'scienceArc', 'iic scienceArc', lampExptime=dcbArcLamps,
                                options=['duplicate', 'cam',
                                         'switchOn', 'warmingTime', 'switchOff'])


class ScienceTrace(SequenceLayout):
    def __init__(self):
        SequenceLayout.__init__(self, 'scienceTrace', 'iic scienceTrace',
                                options=['exptime', 'halogen', 'duplicate', 'cam', 'warmingTime', 'switchOff'])

        for field in self.fields:
            if field.key == 'switchOff':
                field.setText('False')


class Biases(SequenceLayout):
    def __init__(self):
        SequenceLayout.__init__(self, 'biases', 'iic bias', options=['duplicate', 'cam', 'head', 'tail'])


class Darks(SequenceLayout):
    def __init__(self):
        SequenceLayout.__init__(self, 'darks', 'iic dark', exptime=60, options=['duplicate', 'cam', 'head', 'tail'])


class Arcs(SequenceLayout):
    def __init__(self):
        SequenceLayout.__init__(self, 'arcs', 'iic expose arc',
                                options=['exptime', 'argon', 'neon', 'krypton', 'hgar', 'cam', 'switchOn',
                                         'warmingTime', 'switchOff', 'head', 'tail'])


class Flats(SequenceLayout):
    def __init__(self):
        SequenceLayout.__init__(self, 'flats', 'iic expose flat',
                                options=['exptime', 'halogen', 'duplicate', 'cam', 'warmingTime', 'switchOff',
                                         'head', 'tail'])
        for field in self.fields:
            if field.key == 'switchOff':
                field.setText('False')


class SlitThroughFocus(SequenceLayout):
    def __init__(self):
        SequenceLayout.__init__(self, 'slitThroughFocus', 'iic slit throughfocus', position='-5,5,11',
                                options=['exptime', 'argon', 'neon', 'krypton', 'hgar', 'duplicate', 'cam',
                                         'switchOn', 'warmingTime', 'switchOff', 'head', 'tail'])


class DetectorThroughFocus(SequenceLayout):
    def __init__(self):
        SequenceLayout.__init__(self, 'detThroughFocus', 'iic detector throughfocus', position='0,300,11',
                                options=['exptime', 'argon', 'neon', 'krypton', 'hgar', 'tilt', 'duplicate', 'cam',
                                         'switchOn', 'warmingTime', 'switchOff', 'head', 'tail'])


class DitheredArcs(SequenceLayout):
    def __init__(self):
        SequenceLayout.__init__(self, 'ditheredArcs', 'iic ditheredArcs', pixelStep=0.5,
                                options=['exptime', 'argon', 'neon', 'krypton', 'hgar', 'duplicate',
                                         'cam', 'switchOn', 'warmingTime', 'switchOff', 'head', 'tail'])
        for field in self.fields:
            if field.key == 'doMinus':
                field.setText('False')


class DefocusedArcs(SequenceLayout):
    def __init__(self):
        SequenceLayout.__init__(self, 'defocusedArcs', 'iic defocusedArcs', position='-5,5,11',
                                options=['exptime', 'argon', 'neon', 'krypton', 'hgar', 'duplicate', 'cam',
                                         'switchOn', 'warmingTime', 'switchOff', 'head', 'tail'])


class GenericCmd(SequenceLayout):
    def __init__(self):
        SequenceLayout.__init__(self, 'Command', '')
        self.name.setDisabled(True)
        self.comments.setDisabled(True)


class Custom(SequenceLayout):
    def __init__(self):
        SequenceLayout.__init__(self, 'custom', 'iic custom', options=['head', 'tail'])


class Previous(SequenceLayout):
    flagToText = {0: 'OK', 1: 'FAILED', 2: 'aborted', 3: 'finished'}

    def __init__(self):
        QGridLayout.__init__(self)

        self.sequenceId = SpinBox()
        self.seqtypeWidget = Label('previous')
        self.name = LineEdit('')
        self.comments = LineEdit('')
        self.cmdStr = LineEdit('')
        self.cmdStatus = LineEdit('')
        self.cmdOutput = LineEdit('')

        self.addWidget(Label('sequence_id'), 0, 0)
        self.addWidget(self.sequenceId, 0, 1)

        self.addWidget(Label('sequence_type'), 1, 0)
        self.addWidget(self.seqtypeWidget, 1, 1)

        self.addWidget(Label('name'), 2, 0)
        self.addWidget(self.name, 2, 1)

        self.addWidget(Label('comments'), 3, 0)
        self.addWidget(self.comments, 3, 1)

        self.addWidget(Label('cmdStr'), 4, 0)
        self.addWidget(self.cmdStr, 4, 1)

        self.addWidget(Label('didFail'), 5, 0)
        self.addWidget(self.cmdStatus, 5, 1)

        self.addWidget(Label('cmdOutput'), 6, 0)
        self.addWidget(self.cmdOutput, 6, 1)

        [max_sequence_id] = opDB.fetchone('select max(sequence_id) from iic_sequence')
        self.sequenceId.setRange(1, max_sequence_id)
        self.sequenceId.valueChanged.connect(self.load)
        self.sequenceId.setValue(max_sequence_id)

    @property
    def seqtype(self):
        return self.seqtypeWidget.text()

    def load(self):
        query = f'select sequence_type, name, comments, cmd_str, status_flag, cmd_output from iic_sequence ' \
                f'inner join iic_sequence_status on iic_sequence.sequence_id=iic_sequence_status.sequence_id ' \
                f'where iic_sequence.sequence_id={self.sequenceId.value()} '
        try:
            seqtype, name, comments, cmdStr, status_flag, cmd_output = opDB.fetchone(query)
            self.seqtypeWidget.setText(seqtype)
            self.name.setText(name)
            self.comments.setText(comments)
            self.cmdStr.setText(self.reformat(cmdStr))
            self.cmdStatus.setText(Previous.flagToText[int(status_flag)])
            self.cmdOutput.setText(cmd_output)
        except:
            pass

    def reformat(self, cmdStr):
        if 'iic' in cmdStr:
            return cmdStr

        return f"iic {stripQuotes(stripField(stripField(cmdStr, 'name='), 'comments='))}"


class Dialog(QDialog):
    def __init__(self, panelwidget):
        QDialog.__init__(self, panelwidget)
        self.panelwidget = panelwidget
        self.availableSeq = dict(
            masterBiases=MasterBiases,
            masterDarks=MasterDarks,
            ditheredFlats=DitheredFlats,
            scienceArc=ScienceArc,
            scienceTrace=ScienceTrace,
            biases=Biases,
            darks=Darks,
            arcs=Arcs,
            flats=Flats,
            detectorThroughFocus=DetectorThroughFocus,
            ditheredArcs=DitheredArcs,
            defocusedArcs=DefocusedArcs,
            previous=Previous,
            command=GenericCmd,
        )

        vbox = QVBoxLayout()
        self.grid = QGridLayout()
        self.grid.setSpacing(2)

        self.comboLabel = Label('Sequence type')

        self.comboType = ComboBox()
        self.comboType.addItems(list(self.availableSeq.keys()))
        self.comboType.currentIndexChanged.connect(self.showRelevantWidgets)

        self.grid.addWidget(self.comboLabel, 1, 0)
        self.grid.addWidget(self.comboType, 1, 1)
        self.addLayout('', '')
        self.comboType.setCurrentIndex(1)

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
        self.seqLayout.clearLayout()
        self.grid.removeItem(self.seqLayout)
        self.adjustSize()

        try:
            name = self.seqLayout.name.text()
            comments = self.seqLayout.comments.text()

        except Exception as e:
            name = ''
            comments = ''

        self.addLayout(name, comments)

    def addLayout(self, prevName, prevComments):

        obj = self.availableSeq[self.comboType.currentText()]
        self.seqLayout = obj()

        self.grid.addLayout(self.seqLayout, 2, 0, self.seqLayout.rowCount(), self.seqLayout.columnCount())
        self.adjustSize()

        if prevName and not self.seqLayout.name.text():
            self.seqLayout.name.setText(prevName)

        if prevComments and not self.seqLayout.comments.text():
            self.seqLayout.comments.setText(prevComments)

    def addSequence(self):
        seqtype = self.seqLayout.seqtype
        name = str(self.seqLayout.name.text())
        comments = str(self.seqLayout.comments.text())
        cmdStr = str(self.seqLayout.cmdStr.text())

        cmdRow = CmdRow(self.panelwidget, name, comments, cmdStr, seqtype=seqtype)

        self.panelwidget.add(cmdRow=cmdRow)
