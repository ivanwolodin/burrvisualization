# -*- coding: utf-8 -*-

from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtSerialPort import QSerialPortInfo

# как часто проверять он наличии порта
SLEEP_PERIOD_MSEC = 500

class SerialPortChecker(QTimer):
  off = pyqtSignal()
  on = pyqtSignal()
  """
  
  Для проверки наличия опредленного порта используется этот класс
  """

  def __init__(self, parent, mutex):
    super().__init__(parent)
    self.port = ""
    self.port_exist = False
    self.mutex = mutex
    self.timeout.connect( self.safe_run )


  def start(self):
    super().start(SLEEP_PERIOD_MSEC)


  def safe_run(self):
    self.mutex.lock()
    self.run()
    self.mutex.unlock()


  def run(self):
    """
    Собственно сама проверка существования порта
    """
    if self.port == "":
      return

    port_exist = False
    for port_info in QSerialPortInfo().availablePorts():
      if port_info.portName() == self.port:
        port_exist = True
        break

    if port_exist is False and self.port_exist is True:
      self.off.emit()
    elif port_exist is True and self.port_exist is False:
      self.on.emit()

    self.port_exist = port_exist
