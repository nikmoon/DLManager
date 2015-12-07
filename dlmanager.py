#!/usr/bin/python
#coding: utf-8

import sys
import os
from os import path
from PyQt4 import QtCore, QtGui, uic

from tmp import WorkDirectory


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
        self._workDirsList = self._read_workdirs_file()
        self._dialogDir = APP_PATH
        self._activeWorkDir = None
        self._currentIndex = -1;

        self._connect_all()


    def _on_close_app(self, event):
        self._save_workdirs_file()
        if self._activeWorkDir:
            self._activeWorkDir.write_state_file()  # сохраняем состояние текущего рабочего каталога
        event.accept()


    def _connect_all(self):
        '''Устанавливаем все обработчики'''
        self.closeEvent = self._on_close_app                     # делаем все, что нужно при выходе из программы
        self.cboxWorkDirs.currentIndexChanged[int].connect(self._on_change_work_dir)
        self.btnAddWorkDir.clicked.connect(self._add_work_dir)


    def _on_change_work_dir(self, index):
        if index == self._currentIndex:
            return

        # сохраняем состояние текущего рабочего каталога
        if self._activeWorkDir:
            self._activeWorkDir.write_state_file()
            print u'Состояние каталога "{0}" сохранено'.format(self._activeWorkDir.path)

        if index == -1:
            self._activeWorkDir = None
        else:
            # открываем новый рабочий каталог
            self._activeWorkDir = WorkDirectory(unicode(self.cboxWorkDirs.currentText()))
            print u'Текущий каталог: "{0}"'.format(self._activeWorkDir.path)
            self._fill_lw_entries()


    def _fill_lw_entries(self):
        # очищаем QListWidget со списком рабочих элементов
        self.lwEntries.clear()

        # выводим содержимое нового рабочего каталога
        for entry in sorted(self._activeWorkDir.entries):
            entryItem = QtGui.QListWidgetItem(entry, self.lwEntries)



    def _read_workdirs_file(self):
        '''Читаем из файла список рабочих каталогов.
        Все найденные каталоги заносятся в соответствующий ComboBox'''
        workDirsList = []
        if path.exists(self._workDirsFilePath):
            with open(self._workDirsFilePath) as workDirsFile:
                for line in workDirsFile:
                    line = line.decode('utf-8')
                    if line.endswith(u'\n'):
                        line = line[:-1]
                    if line and not line in workDirsList:
                        workDirsList.append(line)
                        self.cboxWorkDirs.addItem(line)
        self.cboxWorkDirs.setCurrentIndex(-1)   # при запуске приложения никакой каталог не выбран
        return workDirsList


    def _save_workdirs_file(self):
        if path.exists(self._workDirsFilePath):
            os.rename(self._workDirsFilePath, self._workDirsFilePath + u'.bak')
        with open(self._workDirsFilePath, 'w') as workDirsFile:
            for dirPath in self._workDirsList:
                workDirsFile.write((dirPath + u'\n').encode('utf-8'))

    def _add_work_dir(self):
        dirPath = QtGui.QFileDialog.getExistingDirectory(self, directory=self._dialogDir)
        if not dirPath.isEmpty():
            dirPath = unicode(dirPath)
            self._dialogDir = path.dirname(dirPath)
            if not dirPath in self._workDirsList:
                self._workDirsList.append(dirPath)
                self.cboxWorkDirs.addItem(dirPath)
                print u'Добавляем рабочий каталог: ', dirPath, type(dirPath)



if __name__ == '__main__':
    APP = QtGui.QApplication(sys.argv)
    mainWindow = MyWidget()
    mainWindow.show()
    sys.exit(APP.exec_())

