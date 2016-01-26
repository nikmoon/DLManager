#
#  -*- coding: utf-8 -*-
#

import os
import os.path as path
import shutil

from LocalLib import check_permissions



class ConfigFile(object):
    '''-------------------------------------------------------------
        Класс для создания конфигурационных файлов и работы с ними
    -------------------------------------------------------------'''   

    BACKUP_EXT = u'.bak'

    def __init__(self, rwList, fileName, dirName = None):

        # если аргумент dirName не задан, значит fileName содержит полный путь к файлу конфигурации
        if dirName is None:
            filePath = fileName
            dirName, fileName = path.split(filePath)
        else:
            filePath = path.join(dirName, fileName)

        # проверим существование каталога, в котором должен находиться файл
        if not path.exists(dirName):
            print u'Directory {0} not exists'.format(dirName)
            raise Exception(u'Directory for config file not exists')

        # мы должны иметь полные права доступа для каталога с файлом
        if not check_permissions(dirName, read=True, write=True, execute=True):
            print u'No rwx permissions for directory {0}'.format(dirName)
            raise Exception(u'No rwx permissions for directory')

        # если файл уже существует, мы должны иметь права на чтение/запись
        if path.exists(filePath):
            if not check_permissions(filePath, read=True, write=True):
                print u'No permissions for file {0}'.format(filePath)
                raise Exception(u'No permissions for config file')

        # сохраняем необходимые значения
        self._fileName = fileName
        self._dirName = dirName
        self._path = filePath
        self._backupPath = self._path + self.BACKUP_EXT
        self._read = rwList[0]
        self._write = rwList[1]


    def read(self):
        if path.exists(self._path):
            cfg = self._read(self._path)
        elif path.exists(self._backupPath):
            cfg = self._read(self._backupPath)
        else:
            cfg = self._read()
        return cfg


    def write(self, cfg):
        self._write(self._path, cfg)
        self.create_backup()


    @property
    def path(self):
        return self._path


    def is_exists(self):
        return path.exists(self._path)


    def truncate(self):
        '''Усечение существующего файла или создание нового'''
        f = open(self._path, 'w')
        f.close()


    def create_backup(self):
        '''Создание бэкапа файла'''
        backupTmp = self._backupPath + u'.tmp'
        shutil.copy(self._path, backupTmp)
        if path.exists(self._backupPath):
            os.remove(self._backupPath)
        shutil.move(backupTmp, self._backupPath)



if __name__ == '__main__':
    '''
    cfgDirList = ConfigFile_DirList(u'/home/nikbird/DLManager')
    dirList = cfgDirList.read()
    for dirName in dirList:
        cfgDirState = ConfigFile_DirState(dirName)
        print dirName
        dirState = cfgDirState.read()
        print dirState
    '''
    pass


