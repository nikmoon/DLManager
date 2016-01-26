#
#  -*- coding: utf-8 -*-
#

import os
import os.path as path


APP_PATH = path.dirname(path.abspath(__file__))


def check_permissions(entryPath, read=True, write=None, execute=None):
    '''----------------------------------------------------------------
        Проверка прав доступа исполняемого кода к указанному файлу.
        Под файлом понимается любой элемент файловой системы.
    ----------------------------------------------------------------'''
    needPerm = 0
    for mask, perm in ((4, read), (2, write), (1, execute) ):
        if perm:
            needPerm += mask
    entryStat = os.stat(entryPath)
    entryPerm = entryStat.st_mode
    if os.geteuid() == entryStat.st_uid:        # если мы - владелец файла
        entryPerm = (entryPerm >> 6) & 0x7
    elif os.getegid() == entryStat.st_gid:      # если мы в группе-владельце
        entryPerm = (entryPerm >> 3) & 0x7
    else:                                       # если мы вообще левые для этого файла
        entryPerm = entryPerm & 0x7
    return bool((entryPerm & needPerm) == needPerm)


