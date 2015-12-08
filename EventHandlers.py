#coding: utf-8


import sys
import os
from os import path
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import Qt

from tmp import check_permissions, WorkDirectory



class EventHandlerWrapper(object):

    def __init__(self, widget):
        self.widget = widget
        self.parent = self.widget.parentWidget()



class EvHandler_WorkDirsCBox(EventHandlerWrapper):
    '''Обертка-обработчик для элемента QComboBox, содержащего список рабочих каталогов'''

    def __init__(self, widget):
        super(EvHandler_WorkDirsCBox, self).__init__(widget)
        self.baseKeyEvent = self.widget.keyPressEvent
        self.widget.keyPressEvent = self.keyPressEvent
        self.widget.currentIndexChanged[int].connect(self._on_change_work_dir)


    def keyPressEvent(self, keyEvent):
        self.baseKeyEvent(keyEvent)


    def _on_change_work_dir(self, index):
        '''Из списка выбран другой рабочий каталог'''
        print 'Каталог был изменен'
        parent = self.parent
        if parent._activeWorkDir:                     # сохраняем состояние текущего рабочего каталога
            parent._activeWorkDir.write_state_file()
            print u'Состояние каталога "{0}" сохранено'.format(parent._activeWorkDir.path)
        if index == -1:
            parent._activeWorkDir = None
            parent.lwEntries.clear()
        else:
            parent._activeWorkDir = WorkDirectory(unicode(self.widget.currentText()))   # открываем новый рабочий каталог
            print u'Текущий каталог: "{0}"'.format(parent._activeWorkDir.path)
            parent._fill_lw_entries()



class EvHandler_EntriesListWidget(EventHandlerWrapper):
    '''Обертка-обработчик для элемента QListWidget, содержащего элементы текущего рабочего каталога'''

    def __init__(self, widget):
        super(EvHandler_EntriesListWidget, self).__init__(widget)
        self.baseKeyEvent = self.widget.keyPressEvent
        self.widget.keyPressEvent = self.keyPressEvent

        # задаем обработчик изменения текущего элемента для отображения ссылок на него
        self.widget.currentRowChanged.connect(self.selected_new_entry)


    def selected_new_entry(self, row):
        parent = self.parent
        if row == -1:
            parent.lwLinks.clear()
            return

        entryItem = self.widget.item(row)
        if entryItem is None:
            return

        parent._fill_lw_links(unicode(entryItem.text()))
        print u'Выбран новый элемент в строке ', row


    def keyPressEvent(self, keyEvent):
        self.baseKeyEvent(keyEvent)
        parent = self.parent
        key = keyEvent.key()
        if key == Qt.Key_Insert:
            parent._add_link()



class EvHandler_Links(EventHandlerWrapper):

    def __init__(self, widget):
        super(EvHandler_Links, self).__init__(widget)
        self.baseKeyEvent = self.widget.keyPressEvent
        self.widget.keyPressEvent = self.keyPressEvent

    def keyPressEvent(self, keyEvent):
        self.baseKeyEvent(keyEvent)
        parent = self.parent
        key = keyEvent.key()

        if key == Qt.Key_Delete:
            if parent._remove_link():
                print u'Удалена ссылка'


