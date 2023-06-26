# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

from abc import ABC, ABCMeta, abstractmethod
from functools import wraps
from typing import Callable
import subprocess

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
        # abstractmethod will automatically raise an error if method is not
        # implemented so seperate raise NotImplementedError is redundant

    @abstractmethod
    def connectObjects(self) -> None:
        '''
        Connects UI elements so they do stuff when interacted with.
        '''

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

class AnalysisTab(AnalysisBase):
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
        
    @staticmethod
    def freezeContinue(func:Callable) -> Callable:
        '''
        Freezes the tab's push button given until func is executed. Can be used
        as a decorator using @AnalysisTab.freezeContinue or as a function using
        AnalysisTab.freezeContinue(func)(self, *args, **kwargs).
        '''
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            '''
            Modification of the original function func.
            '''
            self.push.setEnabled(False)
            self.push.setText("Busy")
            # force pyqt to update button immediately (otherwise pyqt leaves
            # this until the end and nothing happens)
            self.push.repaint()
            value = func(self, *args, **kwargs)
            # func executed, now can unfreeze
            self.push.setEnabled(True)
            self.push.setText("Continue")
            return value
        return wrapper

    def runCmd(self, *args, input:str=None) -> str:
        '''
        This function will run the shell command sent to it and either returns
        and shows the result in the main window's output's text tab or displays
        an error message (in which case None is returned).

        args should be a series of strings with commas representing spaces, eg.
        'ls', '-A', '/home/'. The keyword input_ is the a string to feed to
        stdin after the command execution.
        '''
        try:
            p = subprocess.run(args, universal_newlines=True, input=input,
                               cwd=self.owner.dir_edit.text(), timeout=10,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               check=True)
            self.owner.output_text.setText(p.stdout)
            return p.stdout
        except subprocess.SubprocessError as e:
            self.owner.showError(f'Error ({e.__class__.__name__}): {e}'
                                 f'\n\n{e.stdout}')
            return None
        except FileNotFoundError:
            self.owner.showError('Error (FileNotFoundError)'
                                 '\n\nThis error is likely caused by a quantics '
                                 'program not being installed or being in an '
                                 'invalid directory.')
            return None
        except Exception as e:
            self.owner.showError(f'Error ({e.__class__.__name__})'
                                 f'\n\n{e}')
            return None

