# -*- coding : utf-8 -*-

import time
import UI.mainFm
import Src.startDlg
import Src.parmasDlg
import Src.coolingFm
import Src.control
from MPPCModule.MPPCModule import mppcum1a

from PySide2 import QtCore, QtWidgets, QtGui


class MainFm(QtWidgets.QWidget):

    quit_signal = QtCore.Signal()
    ctrl_init_signal = QtCore.Signal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(self.windowFlags() & ~
                            QtCore.Qt.WindowMaximizeButtonHint)
        self.ui = UI.mainFm.Ui_mainFm()
        self.ui.setupUi(self)

        self.var_init()
        self.connect_init()

    def var_init(self):
        self.Parmas = {}
        self._CYCLE_TIME = 100
        self.DeviceHandle = mppcum1a.INVALID_HANDLE_VALUE
        self.PipeHandle = mppcum1a.INVALID_HANDLE_VALUE

        self.StartDlg = Src.startDlg.StartDlg()
        self.ParmasDlg = Src.parmasDlg.ParmasDlg()
        self.CoolingDlg = Src.coolingFm.CoolingFm()
        self.Ctrler = Src.control.Control()
        self.CtrlThread = QtCore.QThread()
        self.Ctrler.moveToThread(self.CtrlThread)
        self.CtrlThread.start()

    def connect_init(self):
        self.StartDlg.ui.start_Btn.clicked.connect(
            self.startdlg_start_clicked_slot)
        self.ParmasDlg.ui.startBtn.clicked.connect(
            self.parmasdlg_start_clicked_slot)
        self.ctrl_init_signal.connect(self.Ctrler.init)
        self.Ctrler.serial_open_failed_signal.connect(
            self.ctrl_serial_open_failed_slot)
        self.ui.stop_Btn.clicked.connect(self.stop_clicked_slot)

    def start(self):
        self.StartDlg.show()

    def mppc_config(self):
        self.DeviceHandle = mppcum1a.MPPC_OpenDevice()
        if self.DeviceHandle == mppcum1a.INVALID_HANDLE_VALUE:
            MsgBox = QtWidgets.QMessageBox()
            MsgBox.setWindowTitle("！")
            MsgBox.setText("Open Device Error！")
            MsgBox.exec_()
            return False

        self.PipeHandle = mppcum1a.MPPC_OpenPipe(self.DeviceHandle)
        if self.PipeHandle == mppcum1a.INVALID_HANDLE_VALUE:
            MsgBox = QtWidgets.QMessageBox()
            MsgBox.setWindowTitle("！")
            MsgBox.setText("Open Pipe Error！")
            MsgBox.exec_()
            return False

        result = mppcum1a.MPPC_Initialize(self.DeviceHandle)
        if result != mppcum1a.MPPC_SUCCESS:
            MsgBox = QtWidgets.QMessageBox()
            MsgBox.setWindowTitle("！")
            MsgBox.setText("Device Init Error！")
            MsgBox.exec_()
            return False

        result = mppcum1a.MPPC_SetProperty(
            self.DeviceHandle, self.Parmas['gatetime']*1000, self.Parmas['datasize'])
        if result != mppcum1a.MPPC_SUCCESS:
            MsgBox = QtWidgets.QMessageBox()
            MsgBox.setWindowTitle("！")
            MsgBox.setText("Set Property Error！")
            MsgBox.exec_()
            return False

        if self.Parmas['threshold_index'] <= mppcum1a.VTH_75:
            result = mppcum1a.MPPC_SetThreshold(
                self.DeviceHandle, self.Parmas['threshold_index'])
        else:
            result = mppcum1a.MPPC_SetThreshold(
                self.DeviceHandle, self.mppcum1a.VTH_OVER)
        if result != mppcum1a.MPPC_SUCCESS:
            MsgBox = QtWidgets.QMessageBox()
            MsgBox.setWindowTitle("！")
            MsgBox.setText("Set Threshold Error！")
            MsgBox.exec_()
            return False

        flag = -1
        result = mppcum1a.MPPC_GetPeltierControl(self.DeviceHandle, flag)
        if result == mppcum1a.MPPC_SUCCESS:
            if flag == mppcum1a.ENABLE:
                mppcum1a.MPPC_SetPeltierControl(
                    self.DeviceHandle, self.mppcum1a.DISABLE)
        else:
            MsgBox = QtWidgets.QMessageBox()
            MsgBox.setWindowTitle("！")
            MsgBox.setText("Get PeltierControl Error！")
            MsgBox.exec_()
            return False

        while True:
            mppcum1a.MPPC_SetPeltierControl(
                self.DeviceHandle, self.mppcum1a.ENABLE)
            result = mppcum1a.MPPC_GetPeltierStatus(self.DeviceHandle)
            if result == mppcum1a.MPPC_SUCCESS:
                return True
            time.sleep(1)

    def closeEvent(self, event):
        self.CoolingDlg.hide()
        super().closeEvent(event)

    def parmas_load(self):
        self.Parmas['row'] = self.ParmasDlg.Parmas['pic_x_count']
        self.Parmas['col'] = self.ParmasDlg.Parmas["pic_y_count"]
        self.Parmas['x_step'] = round(
            self.ParmasDlg.Parmas['pic_x_len']*400.0/(self.ParmasDlg.Parmas['pic_x_count'] - 1.0))
        self.Parmas['y_step'] = round(
            self.ParmasDlg.Parmas['pic_y_len']*400.0/(self.ParmasDlg.Parmas['pic_y_count'] - 1.0))
        self.Parmas['x_speed'] = self.ParmasDlg.Parmas['mt_x_speed']
        self.Parmas['y_speed'] = self.ParmasDlg.Parmas['mt_y_speed']
        self.Parmas['gatetime'] = int(
            self.ParmasDlg.ui.gatetime_Cmb.currentText())
        self.Parmas['datasize'] = round(
            self._CYCLE_TIME/self.Parmas['gatetime'])
        self.Parmas['threshold_index'] = self.ParmasDlg.Parmas['threshold_index']
        self.Parmas['serial_name'] = self.ParmasDlg.ui.serial_Cmb.currentText()

    @QtCore.Slot()
    def startdlg_start_clicked_slot(self):
        self.StartDlg.hide()
        self.ParmasDlg.show()

    def app_quit(self):
        self.CtrlThread.quit()
        self.CtrlThread.wait()
        self.quit_signal.emit()

    @QtCore.Slot()
    def stop_clicked_slot(self):
        MsgBox = QtWidgets.QMessageBox()
        MsgBox.setText("程序即将退出")
        MsgBox.setInformativeText("是否保存运行信息，等待下次自动运行？")
        MsgBox.setStandardButtons(
            QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard)
        MsgBox.setDefaultButton(QtWidgets.QMessageBox.Save)
        if MsgBox.exec_() == QtWidgets.QMessageBox.Discard:
            self.app_quit()
        else:
            pass

    @QtCore.Slot()
    def ctrl_serial_open_failed_slot(self):
        MsgBox = QtWidgets.QMessageBox()
        MsgBox.setWindowTitle("！")
        MsgBox.setText("串口打开失败！")
        MsgBox.exec_()
        self.app_quit()

    @QtCore.Slot()
    def parmasdlg_start_clicked_slot(self):
        # if len(self.ParmasDlg.ui.serial_Cmb.currentText()) == 0:
        #     MsgBox = QtWidgets.QMessageBox()
        #     MsgBox.setWindowTitle("！")
        #     MsgBox.setText("串口未找到！")
        #     MsgBox.exec_()
        # else:
        self.ParmasDlg.hide()
        self.ParmasDlg.parmas_save()
        self.parmas_load()
        self.show()
        self.CoolingDlg.show()
        # if self.mppc_config() == False:
        #    self.app_quit()
        self.ctrl_init_signal.emit(self.Parmas)
        self.CoolingDlg.hide()
        self.ui.data_Btn.setEnabled(True)
        self.ui.start_Btn.setEnabled(True)
        self.ui.stop_Btn.setEnabled(True)
