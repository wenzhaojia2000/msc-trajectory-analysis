# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

from PyQt5 import QtWidgets, QtCore
from .ui_base import AnalysisMainInterface, AnalysisTabInterface

class AnalysisResults(QtWidgets.QWidget, AnalysisTabInterface):
    '''
    Defines functionality for the "Analyse Results" tab of the analysis
    GUI.
    '''
    def __init__(self, owner:AnalysisMainInterface) -> None:
        '''
        Initiation method.
        '''
        super().__init__(owner=owner, push_name='analres_push',
                         box_name='analres_layout')

    def findObjects(self, push_name, box_name) -> None:
        '''
        Obtains UI elements as instance variables, and possibly some of their
        properties.
        '''
        super().findObjects(push_name, box_name)
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
        Connects UI elements so they do stuff when interacted with.
        '''
        super().connectObjects()
        # show the autocorrelation box when certain result in analyse results
        for radio in self.radio:
            radio.clicked.connect(self.autocolOptionSelected)
        # in autocorrelation box, allow damping order to change if tau nonzero
        self.autocol_tau.valueChanged.connect(self.autocolDampingChanged)

    @QtCore.pyqtSlot()
    def continuePushed(self) -> None:
        '''
        Action to perform when the tab's 'Continue' button is pushed.
        '''
        # additional arguments for autocorrelation options
        autocol_options = [
            str(self.autocol_emin.value()),
            str(self.autocol_emax.value()),
            self.autocol_unit_map[self.autocol_unit.currentIndex()],
            str(self.autocol_tau.value()),
            str(self.autocol_iexp.value())
        ]
        # get objectName() of checked radio button (there should only be 1)
        radio_name = [radio.objectName() for radio in self.radio
                      if radio.isChecked()][0]
        match radio_name:
            case 'analres_1': # plot autocorrelation function
                self.owner.runCmd('rdauto', '-inter')
            case 'analres_2': # plot FT of autocorrelation function
                self.owner.runCmd('autospec', '-inter', '-FT', *autocol_options)
            case 'analres_3': # plot spectrum from autocorrelation function
                self.owner.runCmd('autospec', '-inter', *autocol_options)
            case 'analres_4': # plot eigenvalues from matrix diagonalisation
                self.owner.runCmd('rdeigval', '-inter')

    @QtCore.pyqtSlot()
    def autocolOptionSelected(self) -> None:
        '''
        Shows the autocorrelation options if a valid option is checked.
        '''
        if self.radio[1].isChecked() or self.radio[2].isChecked():
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
