# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

from PyQt5 import QtWidgets, QtCore
from .ui_base import AnalysisBase

class AnalysisResults(QtWidgets.QMainWindow, AnalysisBase):
    '''
    Defines functionality for the "Analyse Results" tab of the analysis
    GUI.
    '''
    def __init__(self, owner:AnalysisBase) -> None:
        '''
        Initiation method. Requires the owner AnalysisMain instance to access
        some of its instance variables.
        '''
        super().__init__()
        self.owner = owner
        # find and connect objects from parent's .ui file
        self.findObjects()
        self.connectObjects()

    def findObjects(self) -> None:
        '''
        Finds objects related to the current tab from the parent AnalysisMain
        instance.
        '''
        self.analres_push = self.owner.findChild(QtWidgets.QPushButton, 'analres_push')
        self.analres_box = self.owner.findChild(QtWidgets.QBoxLayout, 'analres_layout')
        self.analres_radio = [self.analres_box.itemAt(i).widget() \
                               for i in range(self.analres_box.count())]

        # group box "autocorrelation options"
        self.autocol_box = self.owner.findChild(QtWidgets.QGroupBox, 'autocorrelation_box')
        self.autocol_emin = self.owner.findChild(QtWidgets.QDoubleSpinBox, 'emin_spinbox')
        self.autocol_emax = self.owner.findChild(QtWidgets.QDoubleSpinBox, 'emax_spinbox')
        self.autocol_unit = self.owner.findChild(QtWidgets.QComboBox, 'unit_combobox')
        self.autocol_tau = self.owner.findChild(QtWidgets.QDoubleSpinBox, 'tau_spinbox')
        self.autocol_iexp = self.owner.findChild(QtWidgets.QSpinBox, 'iexp_spinbox')
        # box is hidden initially
        self.autocol_box.hide()
        # map of autocol_unit indices to command line argument (labels are different)
        self.autocol_unit_map = {0: "ev", 1: "au", 2: "nmwl", 3: "cm-1", 4: "kcal/mol"}

    def connectObjects(self) -> None:
        '''
        Connects objects so they do stuff when interacted with.
        '''
        self.analres_push.clicked.connect(self.continuePushed)

        # show the autocorrelation box when certain result in analyse results
        for radio in self.analres_radio:
            radio.clicked.connect(self.autocolOptionSelected)
        # in autocorrelation box, allow damping order to change if tau nonzero
        self.autocol_tau.valueChanged.connect(self.autocolDampingChanged)

    @QtCore.pyqtSlot()
    def continuePushed(self) -> None:
        '''
        Action to perform when the tab's 'Continue' button is pushed.
        '''
        # working directory
        abspath = self.owner.dir_edit.text()
        # additional arguments for autocorrelation options
        autocol_options = [
            str(self.autocol_emin.value()),
            str(self.autocol_emax.value()),
            self.autocol_unit_map[self.autocol_unit.currentIndex()],
            str(self.autocol_tau.value()),
            str(self.autocol_iexp.value())
        ]
        # get objectName() of checked radio button (there should only be 1)
        radio_name = [radio.objectName() for radio in self.analres_radio
                      if radio.isChecked()][0]
        match radio_name:
            case 'analres_1': # plot autocorrelation function
                self.owner.runCmd('rdauto', '-i', abspath)
            case 'analres_2': # plot FT of autocorrelation function
                self.owner.runCmd('autospec', '-inter', '-FT', '-i', abspath, *autocol_options)
            case 'analres_3': # plot spectrum from autocorrelation function
                self.owner.runCmd('autospec', '-inter', '-i', abspath, *autocol_options)
            case 'analres_4': # plot eigenvalues from matrix diagonalisation
                self.owner.runCmd('rdeigval', '-inter', '-i', abspath)

    @QtCore.pyqtSlot()
    def autocolOptionSelected(self) -> None:
        '''
        Shows the autocorrelation options if a valid option is checked.
        '''
        if self.analres_radio[1].isChecked() or self.analres_radio[2].isChecked():
            self.autocol_box.show()
        else:
            self.autocol_box.hide()

    @QtCore.pyqtSlot()
    def autocolDampingChanged(self) -> None:
        '''
        Allows the user to change the damping order if the damping time is set
        to non-zero (ie. damping is enabled)
        '''
        if self.autocol_tau.value() == 0.0:
            self.autocol_iexp.setEnabled(False)
        else:
            self.autocol_iexp.setEnabled(True)
