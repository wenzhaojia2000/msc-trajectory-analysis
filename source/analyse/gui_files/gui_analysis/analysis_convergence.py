# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

from PyQt5 import QtWidgets, QtCore
from .ui_base import AnalysisBase

class AnalysisConvergence(QtWidgets.QMainWindow, AnalysisBase):
    '''
    Defines functionality for the "Analyse Convergence" tab of the analysis
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
        self.analconv_push = self.owner.findChild(QtWidgets.QPushButton, 'analconv_push')
        self.analconv_box = self.owner.findChild(QtWidgets.QBoxLayout, 'analconv_layout')
        self.analconv_radio = [self.analconv_box.itemAt(i).widget() \
                               for i in range(self.analconv_box.count())]

    def connectObjects(self) -> None:
        '''
        Connects objects so they do stuff when interacted with.
        '''
        self.analconv_push.clicked.connect(self.continuePushed)

    @QtCore.pyqtSlot()
    def continuePushed(self) -> None:
        '''
        Action to perform when the tab's 'Continue' button is pushed.
        '''
        # working directory
        abspath = self.owner.dir_edit.text()
        # get objectName() of checked radio button (there should only be 1)
        radio_name = [radio.objectName() for radio in self.analconv_radio
                      if radio.isChecked()][0]
        match radio_name:
            case 'analconv_1': # check orthonormality of spfs in psi file
                self.owner.runCmd('ortho', '-i', abspath)
            case 'analconv_2': # check orthonormality of spfs in restart file
                self.owner.runCmd('ortho', '-r', '-i', abspath)
            case 'analconv_3': # plot populations of natural orbitals
                self.owner.runCmd('rdcheck', 'natpop', '1', '1', '-i', abspath)
            case 'analconv_4': # plot populations of grid edges
                self.owner.runCmd('rdgpop', '-i', abspath, '0')
            case 'analconv_5': # plot time-evolution of norm of wavefunction
                self.owner.runCmd('norm', '-inter', '-i', abspath)
            case 'analconv_6': # norm of wavefunction on restart file
                self.owner.runCmd('norm', '-r', '-i', abspath)
