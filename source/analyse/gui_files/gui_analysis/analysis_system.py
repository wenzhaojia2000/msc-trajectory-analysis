# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

from PyQt5 import QtWidgets, QtCore
from .ui_base import AnalysisBase

class AnalysisSystem(QtWidgets.QMainWindow, AnalysisBase):
    '''
    Defines functionality for the "Analyse System Evolution" tab of the
    analysis GUI.
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
        self.push = self.owner.findChild(QtWidgets.QPushButton, 'analsys_push')
        self.box = self.owner.findChild(QtWidgets.QBoxLayout, 'analsys_layout')
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
            case 'analsys_1': # plot 1d density evolution
                self.owner.runCmd('showd1d', '-inter', '-i', abspath, input_='1')
            case 'analsys_2': # plot 2d density evolution
                self.owner.runCmd('showsys', '-i', abspath)
            case 'analsys_3': # plot diabatic state population
                self.owner.runCmd('plstate', '-i', abspath)
            case 'analsys_4': # plot potential energy surface
                self.owner.runCmd('showsys', '-pes', '-i', abspath, input_='1')
