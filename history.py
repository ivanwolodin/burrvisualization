# -*- coding: utf-8 -*-

import collections
import numbers
import os
from datetime import datetime

DT_FORMAT = "%d.%m.%Y %H:%M:%S"


class HistoryItem(object):
    """
    Этот класс определяет набор (dt, x, y, z), где
    - dt - дата и время
    - x, y, z - координаты
    """
    def __init__(self, dt, x, y, z):
        if type(dt) is not datetime:
          raise ValueError("expected valid datetime object. Received: {}".format(type(dt).__name__))

        if not isinstance(x, numbers.Real):
          raise ValueError("expected valid x-coordinate. Received: {}".format(type(x).__name__))

        if not isinstance(y, numbers.Real):
          raise ValueError("expected valid y-coordinate. Received: {}".format(type(y).__name__))

        if not isinstance(z, numbers.Real):
          raise ValueError("expected valid z-coordinate. Received: {}".format(type(z).__name__))

        self.dt = dt.replace(microsecond=0)
        self.x = x
        self.y = y
        self.z = z


    def __str__(self):
        """
        Конвертирует объект в строку. Предполагается использовать для записи в файл
        """
        return "{}\t{}\t{}\t{}".format(
          self.dt.strftime(DT_FORMAT),
          self.x,
          self.y,
          self.z,
        )


    def __repr__(self):
        """
        Формальное строковое представление
        """
        return "{}({}, {}, {}, {})".format(
          self.__class__.__name__,
          self.dt.strftime(DT_FORMAT),
          self.x,
          self.y,
          self.z,
        )


    @staticmethod
    def read_from_string(s):
        """
        Функция, для получения объекта HistoryItem из строки
        """
        parts = s.strip().split()
        # требуется 5 частей: дата, время, x, y, z
        # обычно они разделены пробелами и табуляцией
        if len(parts) < 5:
          raise ValueError("required 5 tokens")
        dt = datetime.strptime(" ".join(parts[0:2]), DT_FORMAT)
        x = float(parts[2])
        y = float(parts[3])
        z = float(parts[4])
        #print(x,y,z)
        # здесь будет стоять обработка
        return HistoryItem(dt, x, y, z)


class History(collections.MutableSequence):
    """
    Этот класс определяет массив (list) элементов HistoryItem
    отличается от обычного массива тем, что тут запрещается вставлять элементы,
    которые не имеют тип HistoryItem

    """
    def __init__(self):
        self.data = []
        # тут будут храниться минимальные и максимальные значения координат
        self.min_x = 0
        self.min_y = 0
        self.min_z = 0
        self.max_x = 0
        self.max_y = 0
        self.max_z = 0

    def assert_valid_value(self, value):
        if type(value) is not HistoryItem:
            raise ValueError("invalid type")

    def update_minmax(self):
        self.max_x = max(list(map(lambda item: item.x, self.data)) + [self.max_x])
        self.min_x = min(list(map(lambda item: item.x, self.data)) + [self.min_x])
        self.max_y = max(list(map(lambda item: item.y, self.data)) + [self.max_y])
        self.min_y = min(list(map(lambda item: item.y, self.data)) + [self.min_y])
        self.max_z = max(list(map(lambda item: item.z, self.data)) + [self.max_z])
        self.min_z = min(list(map(lambda item: item.z, self.data)) + [self.min_z])

    def update_minmax_on_new_value(self, new_value):
        self.max_x = max(new_value.x, self.max_x)
        self.max_y = max(new_value.y, self.max_y)
        self.max_z = max(new_value.z, self.max_z)
        self.min_x = min(new_value.x, self.min_x)
        self.min_y = min(new_value.y, self.min_y)
        self.min_z = min(new_value.z, self.min_z)

    def insert(self, index, value):
        self.assert_valid_value(value)
        self.data.insert(index, value)
        self.update_minmax_on_new_value(value)

    def __delitem__(self, index):
        self.data.__delitem__(index)
        self.update_minmax()

    def __setitem__(self, index, value):
        self.assert_valid_value(value)
        self.data.__setitem__(index, value)
        self.update_minmax_on_new_value(value)

    def __len__(self):
        return self.data.__len__()

    def __getitem__(self, index):
        return self.data.__getitem__(index)

    def __repr__(self):
        return self.data.__repr__()

    def save_to_file(self, filename):
        f = open(filename, "w")
        for item in self.data:
            f.write("{}\n".format( item ))
        f.close()

    @property
    def xlim(self):
        return self.min_x, self.max_x

    @property
    def ylim(self):
        return self.min_y, self.max_y

    @property
    def zlim(self):
        return self.min_z, self.max_z

    @property
    def plot_data(self):
        x = []
        y = []
        z = []
        for item in self.data:
          x.append(item.x)
          y.append(item.y)
          z.append(item.z)
        return x, y, z

    @staticmethod
    def read_from_file(filename):
        history = History()
        f = open(filename, "r")
        if os.stat(filename).st_size == 0:
            raise ValueError()

        # читаем файл построчно
        line_number = 0
        while True:
            line_number += 1
            line = f.readline()
            if line == "":
                break

          # пропускаем пустую строку
            if line.strip() == "":
                continue

            try:
                history.append( HistoryItem.read_from_string(line) )
            except ValueError as e:
                f.close()
                raise ValueError("Error reading line {}: {}".format(line_number, str(e)))

        f.close()
        return history
