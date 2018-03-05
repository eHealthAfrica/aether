# -*- coding: utf-8 -*-
from enum import Enum


class MergeOptions(Enum):
    overwrite = 'overwrite'
    lww = 'last_write_wins'
    fww = 'first_write_wins'


LINKED_DATA_MAX_DEPTH = 3
