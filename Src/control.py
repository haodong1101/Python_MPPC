# -*- coding:utf-8 -*-

import serial
import time
import threading
from PySide2 import QtCore, QtWidgets
from MPPCModule.MPPCModule import mppcum1a


class Control(QtCore.QObject):

    data_trans_signal = QtCore.Signal(str)
    serial_open_failed_signal = QtCore.Signal()

    def __init__(self):
        super().__init__()

        self.Serial = serial.Serial()
        self.ReceiveThread = threading.Thread(target=self.receive_data)
        self.ReceiveThread.setDaemon(True)
        self.AskStopThread = threading.Thread(target=self.ask_stop)
        self.AskStopThread.setDaemon(True)

        self.data_trans_signal.connect(self.data_trans_slot)

        self.serial_init()
        self._BOOL = True
        self._isStop = True
        self.RowN = 1
        self.ColN = 1

    def serial_init(self):
        self.Serial.baudrate = 9600
        self.Serial.bytesize = serial.EIGHTBITS
        self.Serial.parity = serial.PARITY_NONE
        self.Serial.stopbits = serial.STOPBITS_ONE
        self.Serial.timeout = 0.5
        self.Serial.writeTimeout = 0.5

    @QtCore.Slot(dict, result=bool)
    def init(self, Parmas):
        self.Parmas = Parmas
        if self.serial_open(self.Parmas['serial_name']) == False:
            self.serial_open_failed_signal.emit()
            return
        self.mt_speed_config(self.Parmas['x_speed'], self.Parmas['y_speed'])

    def serial_open(self, Port):
        self.Serial.name = Port
        try:
            self.Serial.open()
        except:
            print("Serial open failed!")
            return False

        self.ReceiveThread.start()
        self.AskstopThread.start()
        return True

    def mt_speed_config(self, XSpeed, YSpeed):
        self.Serial.write("VX=%s/" % XSpeed)
        self.Serial.write("VY=%s/" % YSpeed)

    def mt_x_one_step(self, isForward):
        self._BOOL = False
        if isForward == True:
            self.Serial.write("X:%s/" % self.Parmas['x_step'])
        else:
            self.Serial.write("X:-%s/" % self.Parmas['x_step'])
        self._BOOL = True
        self.wait_stop()

    def mt_y_one_step(self):
        self._BOOL = False
        self.Serial.write("Y:%s/" % self.Parmas['y_step'])
        self._BOOL = True
        self.wait_stop()

    def mppc_get_count(self):
        pass

    def wait_stop(self):
        self._isStop = False
        while True:
            if self._isStop == True:
                return

    def ask_stop(self):
        while True:
            if self._BOOL == True:
                self.Serial.write("?ST/")
                time.sleep(0.03)

    def receive_data(self):
        while True:
            ReceiveData = self.Serial.readline()
            self.data_trans_signal.emit(ReceiveData)

    @QtCore.Slot(str)
    def data_trans_slot(self, ReceiveData):
        if ReceiveData.find("ST=00") != -1:
            self._isStop = True
