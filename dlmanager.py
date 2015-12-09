#!/usr/bin/python
#coding: utf-8

import sys
import os
from os import path
from PyQt4 import QtCore, QtGui, uic

from tmp import check_permissions, StateFile, WorkDirectory
from EventHandlers import EvHandler_EntriesListWidget, EvHandler_WorkDirsCBox, EvHandler_Links


QtGui.QApplication.setStyle('plastique')


APP_PATH = path.dirname(path.abspath(__file__))
QAPP = None


class MyWidget(QtGui.QWidget):

    STATE_FILE_NAME = u'workdirs_file.txt'
    UI_FILE = path.join(APP_PATH, u'dlmanager.ui')
    ENTRIES_COLORS = {
        'work': QtGui.QColor(50, 50, 50),
        'new': QtGui.QColor(0, 200, 0),
        'del': QtGui.QColor(200, 0, 0),
    }

    def __init__(self):
        super(MyWidget, self).__init__()
        uic.loadUi(self.UI_FILE, self)
        self._stateFile = StateFile(self.STATE_FILE_NAME, APP_PATH)
        self._workDirsList = self._read_workdirs_file()
        self._dialogDir = APP_PATH
        self._activeWorkDir = None
        self._problemDirs = []

        self._connect_all()


    def dialog_select_dir(self):
        dirPath = QtGui.QFileDialog.getExistingDirectory(self, directory=self._dialogDir)
        if not dirPath.isEmpty():
            dirPath = unicode(dirPath)
            if not check_permissions(dirPath):
                print u'Недостаточно прав для работы с каталогом "{0}"'.format(dirPath)
                return None
            self._dialogDir = path.dirname(dirPath)
            return dirPath
        return None


    def closeEvent(self, event):
        self._save_workdirs_file()
        if self._activeWorkDir:
            self._activeWorkDir.write_state_file()  # сохраняем состояние текущего рабочего каталога
        event.accept()
        print u'Приложение закрывается'


    def _connect_all(self):
        '''Устанавливаем все обработчики'''
        self.btnAddWorkDir.clicked.connect(self._add_work_dir)
        self.btnRemoveWorkDir.clicked.connect(self._remove_work_dir)

        # создаем экземпляры-обертки для обработки событий
        self.cboxWorkDirs_EventWrapper = EvHandler_WorkDirsCBox(self.cboxWorkDirs)
        self.lwEntries_EventWrapper = EvHandler_EntriesListWidget(self.lwEntries)
        self.lwLinks_EventWrapper = EvHandler_Links(self.lwLinks)


    def _fill_lw_entries(self):
        '''Вывод списка элементов текущего рабочего каталога'''
        self.lwEntries.clear()                              # очищаем QListWidget со списком рабочих элементов
        colorsNames = ['work', 'new', 'del']
        for i, entries in enumerate(self._activeWorkDir.split_entries()):
            if entries:
                color = self.ENTRIES_COLORS[colorsNames[i]]
                for entry in sorted(entries):
                    entryItem = QtGui.QListWidgetItem(entry, self.lwEntries)
                    entryItem.setTextColor(color)

    
    def _fill_lw_links(self, entry):
        self.lwLinks.clear()
        for link in self._activeWorkDir.get_entry(entry):
            item = QtGui.QListWidgetItem(link, self.lwLinks)


    def _read_workdirs_file(self):
        '''Читаем из файла список рабочих каталогов.
        Все найденные каталоги заносятся в соответствующий ComboBox.
        Если для каталога отсутствуют необходимые разрешения, он заносится в список проблемных
        '''
        workDirsList = []
        if self._stateFile.exists:
            with open(self._stateFile.path) as workDirsFile:
                for line in workDirsFile:
                    line = line.decode('utf-8')
                    if line.endswith(u'\n'):
                        line = line[:-1]
                    if line and not line in workDirsList:
                        if check_permissions(line):
                            workDirsList.append(line)
                            self.cboxWorkDirs.addItem(line)
                        else:
                            self._problemDirs.append(line)  # разрешения для каталога были изменены и стали недостаточны
        self.cboxWorkDirs.setCurrentIndex(-1)   # при запуске приложения никакой каталог не выбран
        return workDirsList


    def _save_workdirs_file(self):
        '''Сохранение списка рабочих каталогов'''
        self._stateFile.backup()
        with open(self._stateFile.path, 'w') as workDirsFile:
            for dirPath in self._workDirsList:
                workDirsFile.write((dirPath + u'\n').encode('utf-8'))


    def _add_work_dir(self):
        dirPath = self.dialog_select_dir()
        if dirPath is None:
            return
        if not dirPath in self._workDirsList:
            self._workDirsList.append(dirPath)
            self.cboxWorkDirs.addItem(dirPath)
            print u'Добавляем рабочий каталог: ', dirPath, type(dirPath)


    def _remove_work_dir(self):
        if self._activeWorkDir:
            if not self._activeWorkDir.delete_state_file():
                print u'В текущем каталоге есть элементы, на которые есть ссылки'
                return False
            workDir = self._activeWorkDir
            self._activeWorkDir = None
            index = self.cboxWorkDirs.currentIndex()
            self.cboxWorkDirs.setCurrentIndex(-1)
            self._workDirsList.remove(workDir.path)
            self.cboxWorkDirs.removeItem(index)
            print u'Каталог "{0}" удален из списка'.format(workDir.path)
            return True
        return False


    def _add_link(self):
        '''Добавление новой ссылки на элемент'''
        entryItem = self.lwEntries.currentItem()
        if entryItem is None:
            return False
        entryName = unicode(entryItem.text())
        if not self._activeWorkDir.is_entry_exists(entryName):
            return False
        row = self.lwEntries.currentRow()
        destDirPath = self.dialog_select_dir()
        if destDirPath is None:
            return False
        srcDirPath = self._activeWorkDir.path
        srcPath = path.join(srcDirPath, entryName)
        destPath = path.join(destDirPath, entryName)
        try:
            os.symlink(srcPath, destPath)
        except Exception as ex:
            print ex.args[1]
            return False
        else:
            self._activeWorkDir.add_link(entryName, destPath)
            entryItem.setTextColor(self.ENTRIES_COLORS['work'])
            print u'Добавлена ссылка "{0}" для "{1}" '.format(destPath, srcPath)
            self._fill_lw_links(entryName)
            return True


    def _remove_link(self):
        linkItem = self.lwLinks.currentItem()
        if linkItem is None:
            return False

        linkPath = unicode(linkItem.text())
        try:
            os.unlink(linkPath)
        except Exception as ex:
            print ex.args[1]
            return False
        else:
            entryName = unicode(self.lwEntries.currentItem().text())
            linksList = self._activeWorkDir.get_entry(entryName)
            linksList.remove(linkPath)
            #self._activeWorkDir.get_entry(entryName).remove(linkPath)
            self._fill_lw_links(entryName)
            if not linksList:
                self.lwEntries.currentItem().setTextColor(self.ENTRIES_COLORS['new'])
            self.lwEntries.setFocus()
            return True
        



if __name__ == '__main__':
    if not check_permissions(APP_PATH):
        print u'Не хватает файловых привилегий для запуска приложения'
        sys.exit()
    APP = QtGui.QApplication(sys.argv)
    mainWindow = MyWidget()
    mainWindow.show()
    sys.exit(APP.exec_())

