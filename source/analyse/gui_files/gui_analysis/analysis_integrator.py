# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

from pathlib import Path
from PyQt5 import QtWidgets, QtCore
from .ui_base import AnalysisMainInterface, AnalysisTabInterface

class AnalysisIntegrator(QtWidgets.QWidget, AnalysisTabInterface):
    '''
    Defines functionality for the "Analyse Integrator" tab of the analysis
    GUI.
    '''
    def __init__(self, owner:AnalysisMainInterface) -> None:
        '''
        Initiation method.
        '''
        super().__init__(owner=owner, push_name='analint_push',
                         box_name='analint_layout')

    @QtCore.pyqtSlot()
    def continuePushed(self) -> None:
        '''
        Action to perform when the tab's 'Continue' button is pushed.
        '''
        # get objectName() of checked radio button (there should only be 1)
        radio_name = [radio.objectName() for radio in self.radio
                      if radio.isChecked()][0]
        match radio_name:
            case 'analint_1': # analyse step size
                self.owner.runCmd('rdsteps')
            case 'analint_2': # look at timing file
                self.owner.runCmd('cat', './timing')
            case 'analint_3': # type update file
                out = self.owner.runCmd('rdupdate')
                if out is not None:
                    self.owner.plotFromText(out, xlabel="Time (fs)", title="Update file",
                        labels=['Step size (fs)', 'Error of A-vector', 'Error of phi/spfs']
                    )
            case 'analint_4': # plot update step size
                self.owner.runCmd('rdupdate', '-inter', input_='1')
