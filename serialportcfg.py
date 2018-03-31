# -*- coding: utf-8 -*-

from configparser import ConfigParser
import os
import sys

from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt5.QtWidgets import QMessageBox

CFG_FILE = os.path.dirname(os.path.realpath(__file__)) + "/cfg.ini"

DEFAULT_SETTINGS = {
  'port': "",
  'baud_rate': 1200,
  'data_bits': QSerialPort.Data8,
  'parity': QSerialPort.NoParity,
  'stop_bits': QSerialPort.OneStop,
  'flow_control': QSerialPort.NoFlowControl,
}

# словарь допустимых значений для различных параметров подключений
# ВАЖНО: порядок допустимых значений для какого-либо параметра должен совпадать
# с порядком значений из окна настроек COM-порта
VALID_VALUES = {
  'port': [],
  'data_bits': [
    QSerialPort.Data8,
    QSerialPort.Data7,
    QSerialPort.Data6,
    QSerialPort.Data5,
  ],
  'parity': [
    QSerialPort.NoParity,
    QSerialPort.EvenParity,
    QSerialPort.OddParity,
    QSerialPort.SpaceParity,
    QSerialPort.MarkParity,
  ],
  'stop_bits': [
    QSerialPort.OneStop,
    QSerialPort.OneAndHalfStop,
    QSerialPort.TwoStop,
  ],
  'flow_control': [
    QSerialPort.NoFlowControl,
    QSerialPort.SoftwareControl,
    QSerialPort.HardwareControl,
  ],
}

for port_info in QSerialPortInfo().availablePorts():
  VALID_VALUES['port'].append( port_info.portName() )

def is_valid_baud_rate( value ):
  """
  Функция для проверки корректности значения baud_rate
  """
  if type(value) is str:
    try:
      value = int(value)
    except ValueError:
      return False

  return value > 0


def read():
  """
  Функция чтения файла настроек
  """
  result = DEFAULT_SETTINGS.copy()

  cfg = ConfigParser()

  # не удалось прочесть файл - вернуть настройки по-умолчанию
  try:
    r = cfg.read( CFG_FILE )
  except Exception:
    return DEFAULT_SETTINGS

  if len(r) == 0:
    return DEFAULT_SETTINGS

  # в файле должна быть секция main
  if 'main' not in cfg.sections():
    return DEFAULT_SETTINGS

  for key in DEFAULT_SETTINGS.keys():
    if key not in cfg['main']:
      continue

    try:
      if key != 'port':
        value = int(cfg['main'][key])
      else:
        value = cfg['main'][key]
    except ValueError:
      continue

    if key == "baud_rate":
      if is_valid_baud_rate( value ) is False:
        continue
    elif value not in VALID_VALUES[key]:
      continue

    result[ key ] = value

  return result


def save( settings ):
  """
  Процедура сохранения настроек
  """
  cfg = ConfigParser()
  cfg['main'] = DEFAULT_SETTINGS.copy()
  for key in DEFAULT_SETTINGS.keys():
    if key not in settings:
      continue

    if key == "baud_rate":
      if is_valid_baud_rate( settings[key] ) is False:
        continue
    elif settings[key] not in VALID_VALUES[key]:
      continue

    cfg['main'][key] = str(settings[key])

  with open(CFG_FILE, 'w') as f:
    cfg.write(f)
