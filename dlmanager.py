#!/usr/bin/python
#coding: utf-8

import sys
import os
from os import path
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import Qt

from LocalLib import APP_PATH, check_permissions
from ConfigFile import ConfigFile
from WorkDir import WorkDir


QtGui.QApplication.setStyle('plastique')



class MyWidget(QtGui.QWidget):

    CFG_FILE_NAME = u'.dirlist.cfg'
    
    UI_FILE_PATH = path.join(APP_PATH, u'dlmanager.ui')
    ENTRIES_COLORS = {
        'work': QtGui.QColor(50, 50, 50),
        'new':  QtGui.QColor(0, 200, 0),
        'del':  QtGui.QColor(200, 0, 0),
    }
    COLOR_NAMES = ('new', 'work', 'del')

    def __init__(self):
        super(MyWidget, self).__init__()
        uic.loadUi(self.UI_FILE_PATH, self)
        self._cfgFile = ConfigFile([self._read_cfg, self._write_cfg], self.CFG_FILE_NAME, APP_PATH)

        # список рабочих каталогов, для работы с которыми недостаточно прав
        self._problemDirs = []

        # текущий рабочий каталог
        self._activeWorkDir = None

        # словарь рабочих каталогов в виде {u'Путь к каталогу: WorkDir(u'Путь к каталогу')'}
        self._workDirs = self.get_work_dirs()
        self.sync_cboxWorkDirs()
        
        # текущий каталог для диалога выбора каталога
        self._activeDialogDir = APP_PATH

        self.connect_all()


    def _read_cfg(self, cfgFilePath = None):
        '''Чтение файла конфигурации'''
        cfg = []
        if not cfgFilePath is None:
            with open(cfgFilePath) as cfgFile:
                for line in cfgFile:
                    line = line.decode('utf-8').rstrip()
                    if line:
                        cfg.append(line)
        return cfg


    def _write_cfg(self, cfgFilePath, cfg):
        '''Запись файла конфигурации'''
        dirList = []
        with open(cfgFilePath, 'w') as cfgFile:
            for dirPath in cfg:
                dirList.append(dirPath.encode('utf-8') + '\n')
            cfgFile.writelines(dirList)


    def closeEvent(self, event):
        for workDir in self._workDirs.values():
            workDir.save_state()
        self._cfgFile.write(self._workDirs)
        print u'Приложение закрывается'


    def connect_all(self): 
        self.cboxWorkDirs.currentIndexChanged[int].connect(self.on_change_work_dir)
        self.lwEntries.currentRowChanged.connect(self.on_select_new_entry)
        
        self.lwEntries.baseKeyEvent = self.lwEntries.keyPressEvent
        self.lwEntries.keyPressEvent = self.keyPressEvent_lwEntries


    def keyPressEvent_lwEntries(self, keyEvent):
        '''Обработчик нажатий клавиш для виджета lwEntries'''
        modKeys = QtGui.QApplication.keyboardModifiers()
        key = keyEvent.key()
        if (key == Qt.Key_N) and (modKeys & Qt.ControlModifier):    # Ctrl + N - добавляем новую ссылку
            print 'Добавляем новую ссылку на элемент'
            self.add_link()
        if key == Qt.Key_T:
            if modKeys & Qt.ControlModifier:    # Ctrl + T - добавляем новую ссылку
                self.cboxWorkDirs.setCurrentIndex(-1)
        self.lwEntries.baseKeyEvent(keyEvent)


    def dialog_select_dir(self):
        dirPath = QtGui.QFileDialog.getExistingDirectory(self, directory=self._activeDialogDir)
        if not dirPath.isEmpty():
            dirPath = unicode(dirPath)
            if not check_permissions(dirPath, read=True, write=True, execute=True):
                print u'Недостаточно прав для работы с каталогом "{0}"'.format(dirPath)
                return None
            self._activeDialogDir = path.dirname(dirPath)
            return dirPath
        return None


    def add_link(self):
        '''Добавление новой ссылки на файл'''
        try:
            entryItem = self.lwEntries.currentItem()
            entryName = unicode(entryItem.text())
            linksList = self._activeWorkDir.get_entry_links(entryName, None)
            if linksList is None:
                return False
            srcDir = self._activeWorkDir._path
            destDir = self.dialog_select_dir()
            if destDir is None:
                return False
            srcPath = path.join(srcDir, entryName)
            destPath = path.join(destDir, entryName)
            os.symlink(srcPath, destPath)
        except Exception as ex:
            print ex.args[1]
            return False
        else:
            linksList.append(destPath)
            entryItem.setTextColor(self.ENTRIES_COLORS['work'])
            print u'Добавлена ссылка "{0}" для "{1}" '.format(destPath, srcPath)
            self.sync_lwLinks(entryName)
            return True


    def on_change_work_dir(self, index):
        '''Из списка выбран другой рабочий каталог'''
        if index == -1:
            self._activeWorkDir = None
            self.lwEntries.clear()
        else:
            self._activeWorkDir = self._workDirs[unicode(self.cboxWorkDirs.itemText(index))]
            self.sync_lwEntries()


    def on_select_new_entry(self, row):
        '''Текущим выбран новый файл в рабочем каталоге'''
        if row == -1:
            self.lwLinks.clear()
        else:
            entryItem = self.lwEntries.item(row)
            if not entryItem is None:
                self.sync_lwLinks(unicode(entryItem.text()))


    def get_work_dirs(self):
        '''Чтение списка рабочих каталогов'''
        workDirs = {}
        for dirPath in self._cfgFile.read():
            try:
                workDir = WorkDir(dirPath)
                workDirs[dirPath] = workDir
            except Exception as ex:
                print ex
                if not dirPath in self._problemDirs:
                    self._problemDirs.append(dirPath)
        return workDirs


    def sync_cboxWorkDirs(self):
        '''Синхронизация содержимого виджета со списком рабочих каталогов'''
        self.cboxWorkDirs.clear()
        for dirPath in self._workDirs:
            self.cboxWorkDirs.addItem(dirPath)
        self.cboxWorkDirs.setCurrentIndex(-1)   # после синхронизации никакой каталог не выбран


    def sync_lwEntries(self):
        '''Синхронизация содержимого виджета со списком файлов текущего рабочего каталога'''
        self.lwEntries.clear()
        try:
            workEntries, newEntries, removedEntries = self._activeWorkDir.split_entries()
            for i, entries in enumerate([newEntries, workEntries, removedEntries]):
                colorName = self.COLOR_NAMES[i]
                color = self.ENTRIES_COLORS[colorName]
                for entry in sorted(entries):
                    entryItem = QtGui.QListWidgetItem(entry, self.lwEntries)
                    entryItem.setTextColor(color)
        except Exception as ex:
            print u'Исключени: синхронизация виджета lwEntries не удалась'


    def sync_lwLinks(self, entry):
        '''Синхронизация содержимого виджета со списком ссылок текущего выбранного файла'''
        self.lwLinks.clear()
        try:
            for link in self._activeWorkDir.get_entry_links(entry) or [u'[No links...]']:
                item = QtGui.QListWidgetItem(link, self.lwLinks)
        except Exception as ex:
            print u'Исключение: синхронизация виджета lwLinks не удалась'



"""
class MyWidget(QtGui.QWidget):

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
"""



if __name__ == '__main__':
    APP = QtGui.QApplication(sys.argv)
    mainWindow = MyWidget()
    mainWindow.show()
    sys.exit(APP.exec_())


