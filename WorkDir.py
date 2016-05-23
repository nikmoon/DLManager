#
#  -*- coding: utf-8 -*-
#

import os
import os.path as path
import shutil

from LocalLib import check_permissions
from ConfigFile import ConfigFile



class WorkDir(object):

    CFG_FILE_NAME = u'.dirstate.cfg'

    def __init__(self, dirName):
        
        # рабочий каталог должен существовать
        if not path.exists(dirName):
            print u'Working dir {0} not exists'.format(dirName)
            raise Exception(u'Working dir not exists')

        # мы должны иметь полные права доступа к рабочему каталогу
        if not check_permissions(dirName, read=True, write=True, execute=True):
            print u'No rwx permissions for directory {0}'.format(dirName)
            raise Exception(u'No rwx permissions for directory')

        # сохраняем необходимые значения
        self._path = dirName
        self._cfgFile = ConfigFile([self._read_cfg, self._write_cfg], self.CFG_FILE_NAME, dirName)

        self._entries = self._cfgFile.read()
        self.check_entries()


    def _read_cfg(self, cfgFilePath = None):
        cfg = {}
        if not cfgFilePath is None:
            with open(cfgFilePath) as cfgFile:
                for line in cfgFile:
                    line = line.decode('utf-8').rstrip()
                    if not line:
                        continue
                    if not line.startswith(u'/'):
                        linksList = []
                        cfg[line] = linksList
                    else:
                        linksList.append(line)
        return cfg


    def _write_cfg(self, cfgFilePath, cfg):
        with open(cfgFilePath, 'w') as cfgFile:
            for entryName, links in cfg.iteritems():
                if not links:
                    continue
                toWrite = [s.encode('utf-8') + '\n' for s in [entryName] + links]
                cfgFile.writelines(toWrite)



    def get_entries(self):
        return self._entries


    def get_entry_links(self, entry, defVal = None):
        return self._entries.get(entry, defVal)


    def check_entries(self):
        # ищем новые файлы
        for entry in self.get_dir_entries():
            if not entry in self._entries:
                self._entries[entry] = []
        # ищем удаленные файлы и удаляем их из списка
        for entry in self._entries.keys():
            if not path.exists(path.join(self._path, entry)):
                self.delete_links(entry)
                del self._entries[entry]


    def delete_links(self, entry):
        links = self._entries[entry]
        for link in links:
            try:
                os.unlink(link)
            except Exception as ex:
                print 'Error symlink deletion: {0}'.format(link)


    def split_entries(self):
        workEntries = {}
        newEntries = {}
        removedEntries = {}
        for entry in self._entries.keys():
            links = self._entries[entry]
            entryPath = path.join(self._path, entry)
            if not path.exists(entryPath):  # файл был удален
                self.delete_links(entry)
                del self._entries[entry]
            elif not links:                 # новый файл
                newEntries[entry] = links
            else:
                workEntries[entry] = links
        return workEntries, newEntries, removedEntries


    def get_dir_entries(self):
        '''
        Чтение списка файлов в рабочем каталоге.
        Исключаются файлы, начинающиеся с точки '.'
        '''
        return [entry for entry in os.listdir(self._path) if not entry[0] == u'.']


    def save_state(self):
        '''Сохранение состояния рабочего каталога'''
        self._cfgFile.write(self._entries)
        print u'Состояние каталога {} сохранено'.format(self._path)





if __name__ == '__main__':

#    workDir = WorkDir(u'/media/BADDRIVE/Downloads/Torrent')
    workDir = WorkDir(u'/media/BADDRIVE/Downloads/Other')
    for num, entry in  enumerate(workDir.get_dir_entries()):
        print num+1, entry.encode('utf-8')
    print workDir._workEntries

