from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QScrollBar


class CenteredItem(QTableWidgetItem):
    color = {"init": ("#FF7D7D", "#000000"), "valid": ("#7DFF7D", "#000000"), "active": ("#4A90D9", "#FFFFFF"),
             "finished": ("#5f9d63", "#FFFFFF"), "failed": ("#9d5f5f", "#FFFFFF")}

    def __init__(self, cmdRow, attr, typeFunc, lock=False, align=Qt.AlignCenter):
        self.cmdRow = cmdRow
        self.attr = attr
        self.typeFunc = typeFunc
        QTableWidgetItem.__init__(self, str(getattr(cmdRow, attr)))
        self.setTextAlignment(align)

        if lock:
            self.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        back, col = CenteredItem.color[cmdRow.status]

        self.setForeground(QColor(col))
        self.setBackground(QColor(back))

    def valueChanged(self):
        if self.cmdRow.status == 'init':
            val = self.text()
            setattr(self.cmdRow, self.attr, self.typeFunc(val))
        else:
            self.setText(str(getattr(self.cmdRow, self.attr)))


class Table(QTableWidget):
    colwidthRatio = {6: 0.12, 7: 0.15, 8: 0.43, 11: 0.3}
    colnames = ['', '', '', 'Valid', ' Id', 'Type', 'Name', 'Comments', 'CmdStr', 'VisitStart', 'VisitEnd', 'ReturnStr']

    def __init__(self, panelwidget):
        self.panelwidget = panelwidget
        self.controlKey = False

        nbRows = sum([cmdRow.nbRows for cmdRow in self.cmdRows])

        QTableWidget.__init__(self, nbRows, len(Table.colnames))

        self.setHorizontalHeaderLabels(Table.colnames)

        self.verticalHeader().setDefaultSectionSize(6)
        self.verticalHeader().hide()

        rowNumber = 0
        for cmdRow in self.cmdRows:
            cmdRow.rowNumber = rowNumber
            self.setRowHeight(rowNumber, 14)
            self.setRowHeight(rowNumber + 1, 14)

            self.setCellWidget(rowNumber, 0, cmdRow.buttonDelete)
            self.setCellWidget(rowNumber, 1, cmdRow.buttonMoveUp)
            self.setCellWidget(rowNumber + 1, 1, cmdRow.buttonMoveDown)
            self.setCellWidget(rowNumber, 2, cmdRow.buttonEye)
            self.setCellWidget(rowNumber, 3, cmdRow.valid)
            self.setItem(rowNumber, 4, CenteredItem(cmdRow, 'id', int, lock=True))
            self.setItem(rowNumber, 5, CenteredItem(cmdRow, 'seqtype', str, lock=True))
            self.setItem(rowNumber, 6, CenteredItem(cmdRow, 'name', str))
            self.setItem(rowNumber, 7, CenteredItem(cmdRow, 'comments', str))

            nb = 2
            if cmdRow.showSub and cmdRow.subcommands:
                if len(cmdRow.subcommands) > 1:
                    span = len(cmdRow.subcommands)
                    cols = [0, 2, 3, 4, 5, 6, 7]
                    for nb, subcommand in enumerate(cmdRow.subcommands):
                        self.setRowHeight(rowNumber + nb, 16)
                        self.setItem(rowNumber + nb, 8, CenteredItem(subcommand, 'cmdStr', str))
                        self.setItem(rowNumber + nb, 9, CenteredItem(subcommand, 'visitStart', int, lock=True))
                        self.setItem(rowNumber + nb, 10, CenteredItem(subcommand, 'visitEnd', int, lock=True))
                        self.setItem(rowNumber + nb, 11, CenteredItem(subcommand, 'returnStr', str, lock=True))
                    nb += 1
                else:
                    subcommand = cmdRow.subcommands[0]
                    span = 2
                    cols = [0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
                    self.setItem(rowNumber, 8, CenteredItem(subcommand, 'cmdStr', str))
                    self.setItem(rowNumber, 9, CenteredItem(subcommand, 'visitStart', int, lock=True))
                    self.setItem(rowNumber, 10, CenteredItem(subcommand, 'visitEnd', int, lock=True))
                    self.setItem(rowNumber, 11, CenteredItem(subcommand, 'returnStr', str))

            else:
                span = 2
                cols = [0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
                self.setItem(rowNumber, 8, CenteredItem(cmdRow, 'cmdStr', str))
                self.setItem(rowNumber, 9, CenteredItem(cmdRow, 'visitStart', int, lock=True))
                self.setItem(rowNumber, 10, CenteredItem(cmdRow, 'visitEnd', int, lock=True))
                self.setItem(rowNumber, 11, CenteredItem(cmdRow, 'returnStr', str))

            for col in cols:
                self.setSpan(rowNumber, col, span, 1)

            rowNumber += nb

        self.cellChanged.connect(self.userCellChanged)
        self.setFont(self.getFont())
        self.horizontalHeader().setFont(self.getFont(size=11))

        self.setVerticalScrollBar(VScrollBar(self))

    @property
    def cmdRows(self):
        return self.panelwidget.cmdRows

    def resizeEvent(self, event):
        autoResize = [j for j in range(len(Table.colnames)) if j not in Table.colwidthRatio]
        for j in autoResize:
            self.resizeColumnToContents(j)

        remainingWidth = event.size().width() - sum([self.columnWidth(j) for j in autoResize])

        for col, ratio in Table.colwidthRatio.items():
            self.setColumnWidth(col, ratio * remainingWidth)

        QTableWidget.resizeEvent(self, event)

    def getFont(self, size=10):
        font = self.font()
        font.setPixelSize(size)
        return font

    def userCellChanged(self, row, column):
        self.item(row, column).valueChanged()

    def setRowSelected(self, row, bool):
        for col in range(4, 12):
            self.item(row, col).setSelected(bool)

    def selectAll(self):
        for i in range(self.rowCount()):
            try:
                self.setRowSelected(i, True)
            except AttributeError:
                pass

    def keyPressEvent(self, QKeyEvent):

        try:
            if QKeyEvent.key() == Qt.Key_Control:
                self.controlKey = True

            if QKeyEvent.key() == Qt.Key_C and self.controlKey:

                cmdRows = list(set([item.cmdRow for item in self.selectedItems()]))
                sortedRows = sorted([(self.cmdRows.index(cmdRow), cmdRow) for cmdRow in cmdRows], key=lambda t: t[0])
                self.panelwidget.copy([cmdRow for i, cmdRow in sortedRows])

                for range in self.selectedRanges():
                    self.setRangeSelected(range, False)

            elif QKeyEvent.key() == Qt.Key_V and self.controlKey:
                if self.selectedRanges():
                    ind = max([range.bottomRow() for range in self.selectedRanges()]) // 2
                else:
                    ind = len(self.cmdRows)

                self.panelwidget.paste(ind)

            if QKeyEvent.key() == Qt.Key_Delete:
                cmdRows = list(set([item.cmdRow for item in self.selectedItems()]))
                self.panelwidget.remove(cmdRows)

        except KeyError:
            pass

    def keyReleaseEvent(self, QKeyEvent):
        if QKeyEvent.key() == Qt.Key_Control:
            self.controlKey = False


class VScrollBar(QScrollBar):
    def __init__(self, tablewidget):
        self.panelwidget = tablewidget.panelwidget
        QScrollBar.__init__(self, tablewidget)
        self.scrollValue = False

    def setScrollValue(self, value):
        self.scrollValue = value

    def paintEvent(self, event, a=0.058394160, b=0.4671533):
        if self.scrollValue:
            value = min(self.scrollValue, self.maximum())
            self.setValue(value)
            self.scrollValue = False

        QScrollBar.paintEvent(self, event)
