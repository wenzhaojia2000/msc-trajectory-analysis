# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

from abc import ABC, ABCMeta, abstractmethod
from PyQt5 import QtCore

class AnalysisMeta(type(QtCore.QObject), ABCMeta):
    '''
    Allows the AnalysisBase class to extend from Qt's metaclass so multiple
    inheritance from a Qt object doesn't cause metaclass conflict.
    '''
    pass

class AnalysisBase(ABC, metaclass=AnalysisMeta):
    '''
    Abstract base class of main window and analysis tab GUIs.
    '''
    @abstractmethod
    def findObjects(self) -> None:
        '''
        Obtains UI elements as instance variables.
        '''
        raise NotImplementedError

    @abstractmethod
    def connectObjects(self) -> None:
        '''
        Connects UI elements so they do stuff when interacted with.
        '''
        raise NotImplementedError
