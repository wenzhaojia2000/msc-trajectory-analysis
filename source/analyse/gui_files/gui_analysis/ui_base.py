# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

from abc import ABC, ABCMeta, abstractmethod
from PyQt5 import QtWidgets, QtCore, uic

class AnalysisMeta(type(QtCore.QObject), ABCMeta):
    '''
    Allows the AnalysisBase class to extend from Qt's metaclass so multiple
    inheritance from a Qt object doesn't cause metaclass conflict.
    '''

class AnalysisBase(ABC, metaclass=AnalysisMeta):
    '''
    Abstract class of an analysis GUI, of some kind.
    '''
    @abstractmethod
    def findObjects(self) -> None:
        '''
        Obtains UI elements as instance variables, and possibly some of their
        properties.
        '''
        raise NotImplementedError

    @abstractmethod
    def connectObjects(self) -> None:
        '''
        Connects UI elements so they do stuff when interacted with.
        '''
        raise NotImplementedError

class AnalysisMainInterface(AnalysisBase):
    '''
    Abstract class of the analysis main window.
    '''
    def __init__(self, ui_file, *args, **kwargs) -> None:
        '''
        Initiation method. Requires a .ui file generated from Qt designer for
        the base-level UI.
        '''
        super().__init__()
        uic.loadUi(ui_file, self)
        # following requires implementation of the abstract methods
        self.findObjects()
        self.connectObjects()

        # a bool that records whether there is a popup open that is a part of
        # the main program. the program may then have a class instance
        # representing a popup that modifies this bool.
        #
        # the variable exists as overwriting a popup variable (possibly because
        # the program was trying to make another popup) while the previous
        # popup is still being shown causes the program to segfault.
        self.popup_open = False

class AnalysisTabInterface(AnalysisBase):
    '''
    Abstract class of an analysis tab. The tab should have the following:
    
    - One QBoxLayout instance, containing at least one radio button
    - One QPushButton instance (confirming radio button selection)
    '''
    def __init__(self, owner:AnalysisMainInterface, push_name:str, box_name:str,
                 *args, **kwargs) -> None:
        '''
        Initiation method. As a tab is part of the main program, requires the
        owner AnalysisMain instance as an argument, as well as the object
        name of its QPushButton and QBoxLayout instances.
        '''
        super().__init__()
        self.owner = owner
        self.findObjects(push_name, box_name)
        self.connectObjects()

    def findObjects(self, push_name:str, box_name:str):
        '''
        A possibly incomplete implementation of the findObjects method. Any
        derived class can add further implementation to this method by using
        `super().findObjects(push_name, box_name)`.
        '''
        self.push = self.owner.findChild(QtWidgets.QPushButton, push_name)
        self.box = self.owner.findChild(QtWidgets.QBoxLayout, box_name)
        self.radio = [self.box.itemAt(i).widget() for i in range(self.box.count())]

    def connectObjects(self):
        '''
        A possibly incomplete implementation of the connectObjects method. Any
        derived class can add further implementation to this method by using
        `super().connectObjects()`.
        '''
        self.push.clicked.connect(self.continuePushed)

    @abstractmethod
    @QtCore.pyqtSlot()
    def continuePushed(self) -> None:
        '''
        Action to perform when the tab's push button is pushed.
        '''
        raise NotImplementedError
