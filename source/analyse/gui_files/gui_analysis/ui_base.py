# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

from abc import ABC, ABCMeta, abstractmethod
from functools import wraps
from typing import Callable
import re
import subprocess
import numpy as np

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
        # data which may be displayed by the window, and may or may not be
        # interacted with by some its widgets
        self.data = None

class AnalysisTab(AnalysisBase):
    '''
    Abstract class of an analysis tab. The tab should have the following:
    
    - One QBoxLayout instance, containing at least one radio button
    - One QPushButton instance (confirming radio button selection)
    '''
    # overcomplicated regex to match floats. class variable which can be used
    # in derived class methods.
    # [+-]?                   optionally a + or - at the beginning
    # \d+(?:\.\d*)?           a string of digits, optionally with decimal
    #                         point and possibly more digits
    # (?:[eE][+-]?\d+)?       optionally an exponential (e+N, e-N) at the
    #                         end
    # \.\d+                   catches floats that start with decimal like
    #                         .25
    # [+-]?inf|nan            catches weird values like +-inf and nan
    float_regex = re.compile(
        r'([+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?|\.\d+|[+-]?inf|nan)'
    )

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
        'ls', '-A', '/home/'. The keyword input is the a string to feed to
        stdin after the command execution.
        '''
        try:
            p = subprocess.run(args, universal_newlines=True, input=input,
                               cwd=self.owner.dir_edit.text(),
                               timeout=float(self.owner.timeout_spinbox.value()),
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               check=True)
            self.owner.text.setText(p.stdout)
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

    def readFloats(self, iterable:list, floats_per_line:int=None,
                   ignore_regex:re.Pattern|str=None, check:bool=False,
                   write_text:bool=False) -> None:
        '''
        Function that reads a file or list of strings that is formatted in a
        'grid', ie. in the form

        a1.1   a1.2   a1.3   ...   a1.n
        a2.1   a2.2   a2.3   ...   a2.n
        ...    ...    ...    ...   ...
        am.1   am.2   am.3   ...   am.n

        and returns floats found in it in an numpy array. Each cell should be
        in a numeric form that can be converted into a float like 0.123 or
        1.234E-10, etc., and cells are seperated with any number of spaces (or
        tabs).

        iterable must be an iterable: if it is a string, use string.split('\n')
        before using this function.

        The function only adds a row to the final array if and only if there
        are `floats_per_line` floats in the line. If None, matches any number.

        If ignore_regex is set, the function ignores lines that match the
        regex.

        If check is True, raises an exception if the function cannot find any
        floats.

        If write_text is True, writes the file or iterable into the 'Text'
        output tab.
        '''
        data = []
        if write_text:
            # clear text view if write_text is true
            self.owner.text.setText("")
        for line in iterable:
            # write line to text view if write_text is true
            if write_text:
                self.owner.text.append(line[:-1])
            # ignore finding floats on this line if matches regex
            if ignore_regex and re.search(ignore_regex, line):
                continue
            # should find this number of floats per line, if not, ignore
            # that line
            matches = re.findall(self.float_regex, line)
            if floats_per_line and len(matches) != floats_per_line:
                continue
            # regex returns strings, need to convert into float
            data.append(list(map(float, matches)))
        if len(data) == 0:
            # nothing found
            if check:
                raise ValueError('No floats found in iterable')
            else:
                print('[readFloats] No floats found in iterable')
        self.owner.data = np.array(data)
