# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView


def apply_history_data_to_tablewidget(history, widget):
    """
    Функция берет данные из объекта History в указанный QTableWIiget
    """
    widget.clear()
    widget.setRowCount(0)
    widget.setColumnCount(7)

    # прячет боковые заголовки
    widget.verticalHeader().hide()

    # не дает редактировать значения
    widget.setEditTriggers(QTableWidget.NoEditTriggers)

    # растягивает таблицу
    widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) # по ширине
    #widget.verticalHeader().setSectionResizeMode(QHeaderView.Stretch); # по высоте

    widget.setHorizontalHeaderItem(0, QTableWidgetItem("Дата и время"))
    widget.setHorizontalHeaderItem(1, QTableWidgetItem("Координата X"))
    widget.setHorizontalHeaderItem(2, QTableWidgetItem("Координата Y"))
    widget.setHorizontalHeaderItem(3, QTableWidgetItem("Координата Z"))
    widget.setHorizontalHeaderItem(4, QTableWidgetItem("Азимут"))
    widget.setHorizontalHeaderItem(5, QTableWidgetItem("Зенит"))
    widget.setHorizontalHeaderItem(6, QTableWidgetItem("Погрешность"))

    for item in history:
        i = widget.rowCount()
        widget.insertRow(i)
        widget.setItem(i, 0, QTableWidgetItem(str(item.dt)))
        widget.setItem(i, 1, QTableWidgetItem(str(item.x)))
        widget.setItem(i, 2, QTableWidgetItem(str(item.y)))
        widget.setItem(i, 3, QTableWidgetItem(str(item.z)))
