# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

from pathlib import Path
from PyQt5 import QtWidgets, QtCore
from .ui_base import AnalysisBase

class AnalysisIntegrator(QtWidgets.QMainWindow, AnalysisBase):
    '''
    Defines functionality for the "Analyse Integrator" tab of the analysis
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
        self.push = self.owner.findChild(QtWidgets.QPushButton, 'analint_push')
        self.box = self.owner.findChild(QtWidgets.QBoxLayout, 'analint_layout')
        self.radio = [self.box.itemAt(i).widget() for i in range(self.box.count())]

    def connectObjects(self) -> None:
        '''
        Connects objects so they do stuff when interacted with.
        '''
        self.push.clicked.connect(self.continuePushed)

    @QtCore.pyqtSlot()
    def continuePushed(self) -> None:
        '''
        Action to perform when the tab's 'Continue' button is pushed.
        '''
        # working directory
        abspath = self.owner.dir_edit.text()
        # get objectName() of checked radio button (there should only be 1)
        radio_name = [radio.objectName() for radio in self.radio
                      if radio.isChecked()][0]
        match radio_name:
            case 'analint_1': # analyse step size
                self.owner.runCmd('rdsteps', '-i', abspath)
            case 'analint_2': # look at timing file
                self.owner.runCmd('cat', str(Path(abspath)/'timing'))
            case 'analint_3': # type update file
                out = self.owner.runCmd('rdupdate', '-i', abspath)
                if out is not None:
                    self.owner.plotFromText(out, xlabel="Time (fs)", title="Update file",
                        labels=['Step size (fs)', 'Error of A-vector', 'Error of phi/spfs']
                    )
            case 'analint_4': # plot update step size
                self.owner.runCmd('rdupdate', '-inter', '-i', abspath, input_='1')
