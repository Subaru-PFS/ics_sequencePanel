__author__ = 'alefur'

import argparse
import os
import pwd
import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from panelwidget import PanelWidget


class SequencePanel(QMainWindow):
    def __init__(self, reactor, actor, d_width, d_height, cmdrName):
        QMainWindow.__init__(self)
        self.reactor = reactor
        self.actor = actor
        self.display = d_width, d_height
        self.setName("%s.%s" % ("sequencePanel", cmdrName))

        self.setCentralWidget(PanelWidget(self))

        self.show()
        self.resize(920, 300)

    def setName(self, name):
        self.cmdrName = name
        self.setWindowTitle(name)

    def critical(self, message):
        return QMessageBox.critical(self, 'Warning', message, QMessageBox.Ok, QMessageBox.Cancel)

    def closeEvent(self, QCloseEvent):
        self.reactor.callFromThread(self.reactor.stop)
        QCloseEvent.accept()


def main():
    app = QApplication(sys.argv)

    parser = argparse.ArgumentParser()

    parser.add_argument('--name', default=pwd.getpwuid(os.getuid()).pw_name, type=str, nargs='?', help='cmdr name')
    parser.add_argument('--stretch', default=0.6, type=float, nargs='?', help='window stretching factor')

    args = parser.parse_args()

    geometry = app.desktop().screenGeometry()
    import qt5reactor

    qt5reactor.install()
    from twisted.internet import reactor

    import miniActor

    actor = miniActor.connectActor([])

    try:
        ex = SequencePanel(reactor,
                           actor,
                           geometry.width() * args.stretch,
                           geometry.height() * args.stretch,
                           args.name)
    except:
        actor.disconnectActor()
        raise

    reactor.run()
    actor.disconnectActor()


if __name__ == "__main__":
    main()
