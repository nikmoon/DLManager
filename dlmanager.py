#!/usr/bin/python
#coding: utf-8

import sys
import os
from os import path
from PyQt4 import QtCore, QtGui, uic


QtGui.QApplication.setStyle('plastique')


APP_PATH = path.dirname(path.abspath(__file__))
WORKDIRS_FILE = u'workdirs_file.txt'
QAPP = None


class MyWidget(QtGui.QWidget):

    UI_FILE = path.join(APP_PATH, u'dlmanager.ui')

    def __init__(self):
        super(MyWidget, self).__init__()
        uic.loadUi(self.UI_FILE, self)
        self._workDirsFilePath = path.join(APP_PATH, WORKDIRS_FILE)
        self._workDirsList = self.read_workdirs_file()
        self._fill_cboxWorkDirs()

        #self.cboxWorkDirs.currentIndexChanged[int].connect(self.test)


    def read_workdirs_file(self):
        workDirsList = []
        if path.exists(self._workDirsFilePath):
            with open(self._workDirsFilePath) as workDirsFile:
                for line in workDirsFile:
                    line = line.decode('utf-8')
                    if line.endswith(u'\n'):
                        line = line[:-1]
                    if line:
                        workDirsList.append(line)
        return workDirsList


    def _fill_cboxWorkDirs(self):
        for dirPath in self._workDirsList:
            self.cboxWorkDirs.addItem(dirPath)
        self.cboxWorkDirs.setCurrentIndex(-1)


if __name__ == '__main__':
    APP = QtGui.QApplication(sys.argv)
    mainWindow = MyWidget()
    mainWindow.show()
    sys.exit(APP.exec_())
