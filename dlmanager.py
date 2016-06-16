#!/usr/bin/python
#coding: utf-8

import sys
import os
import stat
from os import path
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import Qt

from LocalLib import APP_PATH, check_permissions
#from ConfigFile import ConfigFile
from WorkDir import WorkDir


QtGui.QApplication.setStyle('plastique')



class MyWidget(QtGui.QWidget):

    CFG_FILE_NAME = u'.dirlist.cfg'
    LOCK_FILE_NAME = u'lockfile.lock'
    CFG_FILE_PATH = path.join(APP_PATH, CFG_FILE_NAME)
    LOCK_FILE_PATH = path.join(APP_PATH, LOCK_FILE_NAME)
    
    UI_FILE_PATH = path.join(APP_PATH, u'dlmanager.ui')

    ENTRIES_COLORS = {
        'work': QtGui.QColor(50, 50, 50),
        'new':  QtGui.QColor(0, 200, 0),
        'del':  QtGui.QColor(200, 0, 0),
    }

    COLOR_NAMES = ('new', 'work', 'del')


    def __init__(self):
        super(MyWidget, self).__init__()

        self.lock_app()
        uic.loadUi(self.UI_FILE_PATH, self)
        self._dirList = self._get_dir_list()
        self._activeWorkDir = None
        self.sync_cboxWorkDirs()
        self._activeDialogDir = APP_PATH
        self.connect_all()


    @classmethod
    def lock_app(cls):
        '''Блокируем возможность запуска других экземпляров приложения'''
        f = None
        try:
            f = open(cls.LOCK_FILE_PATH, "w")
            os.fchmod(f.fileno(), 0)
        except Exception:
            raise
        finally:
            if not f is None:
                f.close()


    @classmethod
    def unlock_app(cls):
        # Разблокируем возможность запуска приложения
        if path.exists(cls.LOCK_FILE_PATH):
            os.remove(cls.LOCK_FILE_PATH)


    def _get_dir_list(self):
        '''Получаем список рабочих каталогов'''
        dirList = []
        with open(self.CFG_FILE_PATH) as cfgFile:
            for line in cfgFile:
                line = line.decode('utf-8').rstrip()
                if line:
                    dirList.append(line)
        return dirList


    def _save_dir_list(self):
        '''Сохранение списка рабочих каталогов'''
        dirList = [dirPath.encode('utf-8') + '\n' for dirPath in self._dirList]
        with open(self.CFG_FILE_PATH, 'w') as cfgFile:
            cfgFile.writelines(dirList)


    def closeEvent(self, event):
        '''Действия при закрытии приложения'''
        if not self._activeWorkDir is None:
            self._activeWorkDir.save_state()
        self._save_dir_list()
        self.unlock_app()


    def connect_all(self): 
        '''Соединяем все слоты с сигналами и назначаем обработчики клавиш виджетам'''
        self.cboxWorkDirs.currentIndexChanged[int].connect(self.on_change_work_dir)
        self.lwEntries.currentRowChanged.connect(self.on_select_new_entry)
        self.btnAddWorkDir.clicked.connect(self.add_work_dir)
        self.btnRemoveWorkDir.clicked.connect(self.remove_work_dir)
        
        self.lwEntries.baseKeyEvent = self.lwEntries.keyPressEvent
        self.lwEntries.keyPressEvent = self.keyPressEvent_lwEntries

        self.lwLinks.baseKeyEvent = self.lwLinks.keyPressEvent
        self.lwLinks.keyPressEvent = self.keyPressEvent_lwLinks


    def keyPressEvent_lwEntries(self, keyEvent):
        '''Обработчик нажатий клавиш для виджета lwEntries'''
        modKeys = QtGui.QApplication.keyboardModifiers()
        key = keyEvent.key()
        if (key == Qt.Key_N) and (modKeys & Qt.ControlModifier):    # Ctrl + N - добавляем новую ссылку
            print 'Добавляем новую ссылку на элемент'
            self.add_link()
            keyEvent.accept()
        self.lwEntries.baseKeyEvent(keyEvent)


    def keyPressEvent_lwLinks(self, keyEvent):
        modKeys = QtGui.QApplication.keyboardModifiers()
        key = keyEvent.key()
        if (key == Qt.Key_N) and (modKeys & Qt.ControlModifier):    # Ctrl + N - меняем название ссылки
            print 'Меняем название ссылки'
            self.change_link_filename()
            keyEvent.accept()
        self.lwLinks.baseKeyEvent(keyEvent)


    def change_link_filename(self):
        try:
            linkItem = self.lwLinks.currentItem()
            linkPath = unicode(linkItem.text())
            splitResult = linkPath.rsplit('.', 1)
            newFileName, result = QtGui.QInputDialog().getText(self, u'Ввод данных', u'Имя файла:', text=path.basename(linkPath))
            if result:
                newFilePath = path.join(path.dirname(linkPath), unicode(newFileName))
                print newFilePath
                entryItem = self.lwEntries.currentItem()
                entryName = unicode(entryItem.text())
                links = self._activeWorkDir.get_entry_links(entryName)
                links[links.index(linkPath)] = newFilePath
                os.rename(linkPath, newFilePath)
                self.sync_lwLinks(entryName)
        except Exception as ex:
            print ex.args


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


    def add_work_dir(self):
        # Добавляем новый рабочий каталог
        dirPath = self.dialog_select_dir()
        if dirPath is None:
            return
        if not dirPath in self._dirList:
            try:
                self._dirList.append(dirPath)
                self.cboxWorkDirs.addItem(dirPath)
                print u'Добавили рабочий каталог: ', dirPath, type(dirPath)
            except Exception as ex:
                print ex.args


    def remove_work_dir(self):
        if self._activeWorkDir:
            dirPath = self._activeWorkDir._path
            self._activeWorkDir.save_state()
            self._activeWorkDir = None
            index = self.cboxWorkDirs.currentIndex()
            self.cboxWorkDirs.setCurrentIndex(-1)
            self.cboxWorkDirs.removeItem(index)
            del self._workDirs[dirPath]
            print u'Каталог "{0}" удален из списка'.format(dirPath)
            return True
        return False


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
            print ex.args
            return False
        else:
            linksList.append(destPath)
            entryItem.setTextColor(self.ENTRIES_COLORS['work'])
            if len(linksList) < 2:
                self.ledNewEntries.setText(unicode(int(self.ledNewEntries.text()) - 1))
                self.ledWorkEntries.setText(unicode(int(self.ledWorkEntries.text()) + 1))
            print u'Добавлена ссылка "{0}" для "{1}" '.format(destPath, srcPath)
            self.sync_lwLinks(entryName)
            return True


    def clear_counters(self):
        for counter in [self.ledAllEntries, self.ledNewEntries, self.ledWorkEntries]:
            counter.clear()


    def on_change_work_dir(self, index):
        '''Из списка выбран другой рабочий каталог'''
        if index == -1:
            if not self._activeWorkDir is None:
                self._activeWorkDir.save_state()
                self._activeWorkDir = None
            self.lwEntries.clear()
            self.clear_counters()
        else:
            self._activeWorkDir = WorkDir(unicode(self.cboxWorkDirs.itemText(index)))
            self.sync_lwEntries()
        print("Изменился текущий рабочий каталог")


    def on_select_new_entry(self, index):
        '''Текущим выбран новый файл в рабочем каталоге'''
        if index == -1:
            self.lwLinks.clear()
        else:
            self.sync_lwLinks(unicode(self.lwEntries.item(index).text()))


    def sync_cboxWorkDirs(self):
        '''Синхронизация содержимого виджета со списком рабочих каталогов'''
        self.cboxWorkDirs.clear()
        for dirPath in self._dirList:
            print dirPath
            self.cboxWorkDirs.addItem(dirPath)
        self.cboxWorkDirs.setCurrentIndex(-1)   # после синхронизации никакой каталог не выбран


    def sync_lwEntries(self):
        '''Синхронизация содержимого виджета со списком файлов текущего рабочего каталога'''
        self.lwEntries.clear()
        try:
            workEntries, newEntries, removedEntries = self._activeWorkDir.split_entries()
            self.ledAllEntries.setText(unicode(len(newEntries) + len(workEntries)))
            self.ledNewEntries.setText(unicode(len(newEntries)))
            self.ledWorkEntries.setText(unicode(len(workEntries)))

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
    try:
        mainWindow = MyWidget()
        mainWindow.show()
        sys.exit(APP.exec_())
    finally:
        mainWindow.unlock_app()


