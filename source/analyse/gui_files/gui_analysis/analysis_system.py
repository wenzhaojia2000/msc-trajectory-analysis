# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

from PyQt5 import QtWidgets, QtCore
from .ui_base import AnalysisMainInterface, AnalysisTab

class AnalysisSystem(QtWidgets.QWidget, AnalysisTab):
    '''
    Defines functionality for the "Analyse System Evolution" tab of the
    analysis GUI.
    '''
    def __init__(self, owner:AnalysisMainInterface) -> None:
        '''
        Initiation method.
        '''
        super().__init__(owner=owner, push_name='analsys_push',
                         box_name='analsys_layout')

    @QtCore.pyqtSlot()
    @AnalysisTab.freezeContinue
    def continuePushed(self) -> None:
        '''
        Action to perform when the tab's 'Continue' button is pushed.
        '''
        # get objectName() of checked radio button (there should only be 1)
        radio_name = [radio.objectName() for radio in self.radio
                      if radio.isChecked()][0]
        match radio_name:
            case 'analsys_1': # plot 1d density evolution
                self.runCmd('showd1d', '-inter', input='1')
            case 'analsys_2': # plot 2d density evolution
                self.runCmd('showsys')
            case 'analsys_3': # plot diabatic state population
                self.runCmd('plstate')
            case 'analsys_4': # plot potential energy surface
                self.runCmd('showsys', '-pes', input='1')
