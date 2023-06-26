# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

from PyQt5 import QtWidgets, QtCore
from .ui_base import AnalysisMainInterface, AnalysisTabInterface

class AnalysisConvergence(QtWidgets.QWidget, AnalysisTabInterface):
    '''
    Defines functionality for the "Analyse Convergence" tab of the analysis
    GUI.
    '''
    def __init__(self, owner:AnalysisMainInterface) -> None:
        '''
        Initiation method.
        '''
        super().__init__(owner=owner, push_name='analconv_push',
                         box_name='analconv_layout')

    @QtCore.pyqtSlot()
    def continuePushed(self) -> None:
        '''
        Action to perform when the tab's 'Continue' button is pushed.
        '''
        # get objectName() of checked radio button (there should only be 1)
        radio_name = [radio.objectName() for radio in self.radio
                      if radio.isChecked()][0]
        match radio_name:
            case 'analconv_1': # check orthonormality of spfs in psi file
                self.owner.runCmd('ortho')
            case 'analconv_2': # check orthonormality of spfs in restart file
                self.owner.runCmd('ortho', '-r')
            case 'analconv_3': # plot populations of natural orbitals
                self.owner.runCmd('rdcheck', 'natpop', '1', '1')
            case 'analconv_4': # plot populations of grid edges
                self.owner.runCmd('rdgpop', '0')
            case 'analconv_5': # plot time-evolution of norm of wavefunction
                self.owner.runCmd('norm', '-inter')
            case 'analconv_6': # norm of wavefunction on restart file
                self.owner.runCmd('norm', '-r')
