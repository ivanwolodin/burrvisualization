# -*- coding: utf-8 -*-

import sys
import traceback

from PyQt5.QtWidgets import QDialog, QApplication, QPushButton, QMessageBox
from PyQt5.QtCore import QObject, pyqtSlot, QIODevice, pyqtSignal
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt5 import uic

import serialportcfg as cfg

class SerialPortConfigDialog(QDialog):
  """
  Класс определяющий окна с настройками ком порта
  """

  def __init__(self, parent = None):
    super().__init__(parent)
    self.setupUi()
    self.setupActions()
    self.okClicked = False


  def setupUi(self):
    """
    Процедура создания графического интерфейса
    """
    uic.loadUi("serialportcfgdialog.ui", self)
    combo_boxes = {
      'data_bits': self.dataBitsComboBox,
      'parity': self.parityComboBox,
      'stop_bits': self.stopBitsComboBox,
      'flow_control': self.flowControlComboBox,
    }

    try:
      settings = cfg.read()

      for key, combo_box in combo_boxes.items():
        index = cfg.VALID_VALUES[key].index( settings[key] )
        combo_box.setCurrentIndex( index )

      self.baudRateComboBox.setEditText( str(settings['baud_rate']) )

      # тут перечисляем порты. Также ставим значение по умолчанию
      for port in cfg.VALID_VALUES['port']:
        self.portComboBox.addItem( port )
        if port == settings['port']:
          self.portComboBox.setCurrentIndex( self.portComboBox.count() - 1 )

    except Exception as e:
      msg = QMessageBox(self)
      msg.setIcon(QMessageBox.Critical)
      msg.setText("Ошибка при чтении настроек")
      msg.setInformativeText(str(e))
      msg.setWindowTitle("Ошибка")
      msg.setDetailedText(traceback.format_exc())
      msg.exec_()
      self.close()

    self.settings = settings


  def setupActions(self):
    """
    Привязка различных действий. Например при нажатии кнопочек
    """
    self.okButton.clicked.connect(self.onOkClick)
    self.cancelButton.clicked.connect(self.onCancelClick)


  def onOkClick(self):
    """
    Процедура проверки и сохранения настроек
    """

    port_value = self.portComboBox.currentText()

    # это проверка значения baud rate
    if cfg.is_valid_baud_rate( self.baudRateComboBox.currentText() ) is False:
      msg = QMessageBox(self)
      msg.setIcon(QMessageBox.Critical)
      msg.setText("Неверное значение baud rate")
      msg.setWindowTitle("Ошибка")
      msg.exec_()
      return
    else:
      baud_rate_value = int(self.baudRateComboBox.currentText())

    # проверка значения dataBits
    try:
      data_bits_value = int(self.dataBitsComboBox.currentText())
    except ValueError:
      msg = QMessageBox(self)
      msg.setIcon(QMessageBox.Critical)
      msg.setText("Неверное значение data bits")
      msg.setWindowTitle("Ошибка")
      msg.exec_()
      return

    parity_value = cfg.VALID_VALUES['parity'][ self.parityComboBox.currentIndex() ]
    stop_bits_value = cfg.VALID_VALUES['stop_bits'][ self.stopBitsComboBox.currentIndex() ]
    flow_control_value = cfg.VALID_VALUES['flow_control'][ self.flowControlComboBox.currentIndex() ]

    self.settings = {
      'port': port_value,
      'baud_rate': baud_rate_value,
      'data_bits': data_bits_value,
      'parity': parity_value,
      'stop_bits': stop_bits_value,
      'flow_control': flow_control_value,
    }

    try:
      cfg.save(self.settings)
    except Exception as e:
      msg = QMessageBox(self)
      msg.setIcon(QMessageBox.Critical)
      msg.setText("Ошибка при записи настроек")
      msg.setInformativeText(str(e))
      msg.setWindowTitle("Ошибка")
      msg.setDetailedText(traceback.format_exc())
      msg.exec_()

    self.okClicked = True
    self.close()


  def onCancelClick(self):
    """
    Настройки не сохраняются. Просто закрываем окно
    """
    self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = SerialPortConfigDialog()
    win.show()
    sys.exit(app.exec_())
