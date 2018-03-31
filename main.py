#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
import traceback
import sys

from tkinter import Tk
# from PyQt5.QtWidgets import QApp
#
# screen = app.primaryScreen()
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QWidget, QLabel, QMainWindow, QFileDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QMutex
from PyQt5 import uic

import numpy as np
import matplotlib as mpl
#from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.backends.backend_qt5agg import FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt5.QtCore import QIODevice

from history import History, HistoryItem
import serialportcfg as cfg
from serialportcfgdialog import SerialPortConfigDialog
from serialportchecker import SerialPortChecker
from helpers import *

# тут устанавливаю размер названий осей
mpl.rcParams['axes.labelsize'] = 15

# это название программы
TITLE = "Визуализационная программа"

class NavigationToolbar(NavigationToolbar2QT):
    # only display the buttons we need
    toolitems = [t for t in NavigationToolbar2QT.toolitems if
                 t[0] in ('Home', 'Pan', 'Zoom', 'Save')]

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.filename = None
        self.z0 = None
        self.askToSave = False

        self.mutex = QMutex() # Не очень понятно, зачем здесь мьютекс
        self.checker = SerialPortChecker(self, self.mutex) # альзо нихтЪ клар
        self.checker.start()

        self.setupUi()
        self.setupActions()
        self.setupSerialPort()
        self.applyNewHistory(History()) # что же у нас в классе History??

    def get_monitor_size(self):
        root = Tk()
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        return width, height

    def setupUi(self):
        """
        Процедура создания графического интерфейса

        """

        uic.loadUi("mainwindow.ui", self)
        # TODO: добавить фиксированный размер главного окна!
        self.setMinimumSize(self.get_monitor_size()[0] * 0.60,
                            self.get_monitor_size()[1] * 0.78)
        self.canvas = FigureCanvas(plt.figure())
        self.tab1Layout.addWidget(self.canvas)
        self.navtoolbar = NavigationToolbar(self.canvas, self.tab1)
        self.tab1Layout.addWidget(self.navtoolbar)
        self.statusbarlabel = QLabel()
        self.statusbar.insertPermanentWidget(0, self.statusbarlabel)
        self.setWindowTitle(TITLE)
        self.tabWidget.setTabText(0, "График")
        self.tabWidget.setTabText(1, "Таблица")




    def setupActions(self):
        """
        Привязка различных действий. Например при нажатии кнопочек или менюшек

        """
        self.fileOpenAction.triggered.connect(self.onOpenActionClick)
        self.fileSaveAction.triggered.connect(self.onSaveActionClick)
        self.fileSaveAsAction.triggered.connect(self.onSaveAsActionClick)
        self.quitAction.triggered.connect(self.close)
        self.serialPortConfigAction.triggered.connect(self.onSerialPortConfigActionClick)
        self.checker.on.connect(self.onSerialTurnedOn)
        self.checker.off.connect(self.onSerialTurnedOff)


    def setupSerialPort(self):
        """
        Процедура установки различных параметров для ком-порта

        """
        self.serial = QSerialPort()
        self.serial.readyRead.connect(self.onDataRecv)

        try:
            settings = cfg.read()
        except Exception as e:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Ошибка при чтении настроек ком-порта")
            msg.setInformativeText(str(e))
            msg.setWindowTitle("Ошибка")
            msg.setDetailedText(traceback.format_exc())
            msg.exec_()
            return

        if len(cfg.VALID_VALUES['port']) == 0:
            self.setSerialStatus("COM-порты не найдены", False)
            return

        elif settings['port'] not in cfg.VALID_VALUES['port']:
            dialog = SerialPortConfigDialog(self)
            dialog.exec_()
            if dialog.okClicked:
                settings = dialog.settings
            else:
                self.setSerialStatus("COM-порт не настроен", False)
            return

        self.setSerialSettings( settings )
        self.startSerial()

    def onSerialTurnedOn(self):
        """
        Вызывается, если соединенился с ком-портом

        """
        self.startSerial()

    def onSerialTurnedOff(self):
        """
        Вызывается, если соединение разорвано

        """
        self.setSerialStatus("Соединение разорвано!", False)
        self.serial.close()

    def startSerial(self):
        """
        Метод для соединения с ком-портом

        """
        if self.serial.isOpen():
            self.serial.close()

        r = self.serial.open(QIODevice.ReadOnly)

        if r is False:
            self.setSerialStatus("Не соединен. Причина: {} ({})".format(self.serial.errorString(),
                                                                        self.serial.error()),
                                                                        False)

        else:
            self.setSerialStatus("Соеденен с портом {}".format(self.serial.portName()), True)

    def setSerialStatus(self, message, good=None):
        """
        Меняет статус бар

        """
        if good is None:
            self.statusbarlabel.setStyleSheet("color: black")
            self.centralwidget.setStyleSheet("")
        elif good:
            self.statusbarlabel.setStyleSheet("color: green")
            self.centralwidget.setStyleSheet("")
        else:
            self.statusbarlabel.setStyleSheet("color: red")
            self.centralwidget.setStyleSheet("background-color: #ffe6e6")
        self.statusbarlabel.setText(message)

    def setSerialSettings(self, settings):
        """
        Процедура установки параметров ком-порта

        """
        self.mutex.lock()
        self.serial.setPortName(settings['port'])
        self.checker.port = settings['port']
        self.mutex.unlock()
        self.serial.setBaudRate(settings['baud_rate'])
        self.serial.setDataBits(settings['data_bits'])
        self.serial.setStopBits(settings['stop_bits'])
        self.serial.setFlowControl(settings['flow_control'])
        self.serial.setParity(settings['parity'])

    def onDataRecv(self):
        """
        Процедура принятия данных из COM-порта

        """
        # описание демонстрационного формата:
        # три значения представлены в виде строк разделенных пробелом

        # перевод данных в строку
        s = self.serial.read(100).decode('utf-8')

        # разделения строки на массив
        parts = s.split()

        # тут проверяется, что в массиве 3 строки как-минимум
        if len(parts) < 3:
            print("not enough parts")
            return

        # тут парсится первые 3 части массива
        values = []
        for i in range(3):
            try:
                values.append(float(parts[i]))
            except ValueError:
                print("invalid token #{}: {}".format(i+1, parts[i]))
                return

        print("new data: {}".format(values))
        self.onHistoryItemAdd(*values)

    def enableSaveActions(self, onlySaveAs = False):
        self.fileSaveAsAction.setEnabled(True)
        if onlySaveAs:
            return
        self.fileSaveAction.setEnabled(True)

    def drawZ0(self):
        """
        Метод перерисовки плоскости z = 0

        """
        STEPS = 10 # количество делений
        range_x = np.arange(self.history.min_x,
                            self.history.max_x,
                            (self.history.max_x - self.history.min_x) / STEPS)

        range_y = np.arange(self.history.min_y,
                            self.history.max_y,
                            (self.history.max_y - self.history.min_y) / STEPS)

        xx, yy = np.meshgrid(range_x, range_y)
        zz = np.zeros((STEPS, STEPS))
        if self.z0:
            self.z0.remove()

        self.ax.legend(('Поверхность Земли',), loc=1, prop={'size': 18, })
        leg = self.ax.get_legend()
        leg.legendHandles[0].set_color('green')
        #leg.legendHandles[1].set_color('blue')
        self.z0 = self.ax.plot_surface(xx, yy, zz, color="green")


    def onSerialPortConfigActionClick(self):
        """
        Событие, когда пользователь нажимает на "Настройка ком-порта"
        """
        dialog = SerialPortConfigDialog(self)
        dialog.exec_()
        if (dialog.okClicked):
            self.setSerialSettings(dialog.settings)
            self.startSerial()

    def applyNewHistory(self, history):
        self.history = history

        apply_history_data_to_tablewidget(self.history, self.historyTableWidget)

        self.tab1Layout.removeWidget(self.canvas)
        self.tab1Layout.removeWidget(self.navtoolbar)
        self.fig = plt.figure()
        self.fig.suptitle('Визуализационный график', fontsize=34)

        self.canvas = FigureCanvas(self.fig)
        self.tab1Layout.addWidget(self.canvas)
        self.navtoolbar = NavigationToolbar(self.canvas, self.tab1)
        self.tab1Layout.addWidget(self.navtoolbar)

        self.ax = self.fig.gca(projection='3d',
                               xlabel="X",
                               ylabel="Y",
                               zlabel="Z",
                               #label='curve'
                               )

        #leg = self.ax.get_legend()
        #leg.legendHandles.set_color('blue')

        self.lines = self.ax.plot(*self.history.plot_data)[0]
       # self.ax.legend(('curve',), loc=2, prop={'size': 18, })

    def onOpenActionClick(self):
        """
        Событие, когда пользователь нажимает на "Открыть файл"

        """
        filename, _  = QFileDialog.getOpenFileName(self, "Открыть файл", ".", "*.txt")
        if filename:
            self.filename = filename
        else:
            return

        try:
            history = History.read_from_file(self.filename)
        except Exception as e:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Ошибка при чтении данных")
            msg.setInformativeText(str(e))
            msg.setWindowTitle("Ошибка")
            msg.setDetailedText(traceback.format_exc())
            msg.exec_()
            return

        self.applyNewHistory(history)
        self.drawZ0()

        self.enableSaveActions( onlySaveAs = True )

    def onSaveActionClick(self):
        """
        Событие, когда пользователь нажимает на "Сохранить файл". Может вызываться вручную
        """
        if not self.filename:
            return self.onSaveAsActionClick()

        # собственно само сохранение - тут
        try:
            self.history.save_to_file(self.filename)
            return True
        except Exception as e:
            self.filename = None
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Ошибка при сохранении данных")
            msg.setInformativeText(str(e))
            msg.setWindowTitle("Ошибка")
            msg.setDetailedText(traceback.format_exc())
            msg.exec_()
            return False

    def onSaveAsActionClick(self):
        """
        Событие, когда пользователь нажимает на "Сохранить файл как". Может вызываться вручную

        """
        self.filename, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", "", "*.txt")
        if self.filename:
            return self.onSaveActionClick()
        else:
            return False

    def onHistoryItemAdd(self, x, y, z):
        """
        При появлении новых данных вызывается этот метод
        """
        # x=0
        self.history.append(HistoryItem(datetime.now(), x, y, z))

        xs, ys, zs = self.history.plot_data
        self.lines.set_data(xs, ys)
        self.lines.set_3d_properties(zs)

        # пересчитываем границы на осях
        # по какой-то неизвестной причине ax.relim не работает
        # поэтому приходится вручную указывать границы
        # благо объект History уже все посчитал
        self.ax.set_xlim(*self.history.xlim)
        self.ax.set_ylim(*self.history.ylim)
        self.ax.set_zlim(*self.history.zlim)
        self.drawZ0()
        self.canvas.draw() #  перерисовка графика

        # это обновляет виджет с таблицей
        apply_history_data_to_tablewidget(self.history, self.historyTableWidget)

        self.askToSave = True
        self.enableSaveActions()

    def closeEvent(self, event):
        """
        Когда окно закрывается, вызывается эта процедура
        """

        # тут спрашивается "Может быть сохранить?"
        # если нажали отмена, или нажали да, а потом передумали - закрытие отменяется
        if self.askToSave:
            r = QMessageBox.question(
            self,
            "Сохранить",
            "Новые данные не были сохранены. Сохранить?",
            buttons = QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            defaultButton = QMessageBox.Yes
            )
            if r == QMessageBox.Yes:
                if self.onSaveActionClick() == False:
                    event.ignore()
                    return
            elif r == QMessageBox.Cancel:
                event.ignore()
                return

        # закрываем тред с проверкой
        self.checker.stop()

        # прячем окно. Закрытие ком-порта может быть долгим
        self.hide()

        # закрываем com-порт
        if self.serial.isOpen():
            self.serial.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec_())
