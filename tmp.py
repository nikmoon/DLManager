#coding: utf-8


import os
from os import path



def check_permissions(entryPath):
    entryStat = os.stat(entryPath)
    # если мы - владелец элемента
    if os.geteuid() == entryStat.st_uid:
        return (entryStat.st_mode >> 6) & 07 == 07
    # если мы в группе-владельце
    elif os.getegid() == entryStat.st_gid:
        return (entryStat.st_mode >> 3) & 07 == 07
    # если мы вообще левые для этого элемента
    else:
        return entryStat.st_mode & 07 == 07



class StateFile(object):

    BACKUP_EXT = u'.bak'

    def __init__(self, fileName, dirPath = None):
        if dirPath is None:     # значит fileName содержит полное имя файла
            filePath = fileName
        else:
            filePath = path.join(dirPath, fileName)
        self._path = filePath
        self._pathBackup = self._path + self.BACKUP_EXT

    @property
    def path(self):
        return self._path


    @property
    def pathBackup(self):
        return self._pathBackup

    @property
    def exists(self):
        return path.exists(self._path)


    def backup(self):
        if self.exists:
            if path.exists(self._pathBackup):
                os.remove(self._pathBackup)
            os.rename(self._path, self._pathBackup)


    def remove(self):
        for filePath in [self._path, self._pathBackup]:
            if path.exists(filePath):
                os.remove(filePath)


class WorkDirectory(object):

    STATE_FILE_NAME = u'dlman.dir.state'

    def __init__(self, dirPath):
        '''Каталог dirPath должен существовать'''
        self._path = dirPath
        self._stateFile = StateFile(self.STATE_FILE_NAME, self._path)
        #self._stateFilePath = path.join(self._path, STATEFILE_NAME)
        self._entries = self.read_state_file()
        self.update_entries()


    def add_link(self, entry, link):
        self._entries[entry].append(link)

    @property
    def path(self):
        return self._path


    @property
    def entries(self):
        entries = {}
        for entry in self._entries:
            entries[entry] = self._entries[entry]
        return entries


    def get_entry(self, entry):
        return self._entries.get(entry)


    def update_entries(self, entryList = None):
        '''Добавляем в список рабочих элементов новые элементы каталога'''
        if entryList is None:
            entryList = self.get_dir_entries()
        for entry in entryList:
            if not entry in self._entries:
                self._entries[entry] = []


    def get_dir_entries(self):
        '''Получить список элементов каталога
        Файл состояния удаляется из списка
        '''
        entries = [entry for entry in os.listdir(self._path) if not (self.STATE_FILE_NAME in entry or entry.startswith(u'.'))]
        return entries


    def is_entry_exists(self, entryName):
        return path.exists(path.join(self._path, entryName))


    def read_state_file(self):
        '''Чтение файла состояния каталога'''
        entries = {}
        if not self._stateFile.exists:
            return entries
        with open(self._stateFile.path) as stateFile:
            for line in stateFile:
                line = line.decode('utf-8')
                if line.endswith(u'\n'):
                    line = line[:-1]
                if not line:
                    continue
                if not line.startswith(u'/'):
                    entryName = line
                    entries[entryName] = []
                else:
                    entries[entryName].append(line)
        return entries


    def write_state_file(self):
        '''Сохранение файла состояния каталога
        Сохраняются только сведения об элементах, на которые имеются ссылки
        '''
        self._stateFile.backup()
        with open(self._stateFile._path, 'w') as stateFile:
            for entryName in self._entries:
                if self._entries[entryName]:
                    writeList = [entryName + u'\n']
                    for symLink in self._entries[entryName]:
                        writeList.append(symLink + u'\n')
                    stateFile.write(u''.join(writeList).encode('utf-8'))


    def delete_state_file(self):
        if self.get_linked_entries_count():
            return False
        self._stateFile.remove()
        return True


    def get_entries_count(self):
        '''Получить количество рабочих элементов'''
        return len(self._entries)


    def get_linked_entries_count(self):
        '''Получить количество элементов, на которые есть ссылки'''
        return len([True for linksList in self._entries.itervalues() if linksList])


    def split_entries(self):
        '''Разбиваем словарь рабочих элементов на 3 словаря:
        1 - существующие элементы, на которые уже есть ссылки;
        2 - существующие элементы, на которые еще нет ссылок;
        3 - несуществующие элементы'''
        workEntries = {}
        newEntries = {}
        removedEntries = {}
        for entry in self._entries:
            if not self.is_entry_exists(entry):
                removedEntries[entry] = self._entries[entry]
            elif len(self._entries[entry]) == 0:
                newEntries[entry] = self._entries[entry]
            else:
                workEntries[entry] = self._entries[entry]
        return workEntries, newEntries, removedEntries



if __name__ == '__main__':

    print check_permissions(u'/home/vasya/DLManager')
