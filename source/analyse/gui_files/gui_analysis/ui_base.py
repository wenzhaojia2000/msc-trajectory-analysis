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
    Allows the AnalysisBase class to extend from ABC's metaclass so multiple
    inheritance from a Qt object and an abstract class doesn't cause metaclass
    conflict.
    '''

class AnalysisBase(QtCore.QObject, metaclass=AnalysisMeta):
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

class AnalysisMainInterface(AnalysisBase, ABC):
    '''
    Abstract class of the analysis main window.
    '''
    def __init__(self, ui_file, *args, **kwargs) -> None:
        '''
        Initiation method. Requires a .ui file generated from Qt designer for
        the base-level UI.
        '''
        super().__init__(*args, **kwargs)
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

    def __init__(self, parent:AnalysisMainInterface, push_name:str, box_name:str,
                 *args, **kwargs) -> None:
        '''
        Initiation method. As a tab is part of the main program, requires the
        parent AnalysisMain instance as an argument, as well as the object
        name of its QPushButton and QBoxLayout instances.
        '''
        super().__init__(parent, *args, **kwargs)
        self.findObjects(push_name, box_name)
        self.connectObjects()

    def findObjects(self, push_name:str, box_name:str):
        '''
        A possibly incomplete implementation of the findObjects method. Any
        derived class can add further implementation to this method by using
        `super().findObjects(push_name, box_name)`.
        '''
        self.push = self.parent().findChild(QtWidgets.QPushButton, push_name)
        self.box = self.parent().findChild(QtWidgets.QBoxLayout, box_name)
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

    @staticmethod
    def freezeContinue(func:Callable) -> Callable:
        '''
        Freezes the tab's push button given until func is executed. Can be used
        as a decorator using @AnalysisTab.freezeContinue or as a function using
        AnalysisTab.freezeContinue(func)(self, *args, **kwargs).
        
        Note: If func raises an exception, continue will not be restored. You
        should ensure func does not crash by eg. wrapping it in a try-except
        block.
        '''
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            '''
            Modification of the original function func.
            '''
            # set cursor to wait cursor
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            self.push.setEnabled(False)
            self.push.setText("Busy")
            # force pyqt to update button immediately (otherwise pyqt leaves
            # this until the end and nothing happens)
            self.push.repaint()
            value = func(self, *args, **kwargs)
            # func executed, now can unfreeze
            QtWidgets.QApplication.restoreOverrideCursor()
            self.push.setEnabled(True)
            self.push.setText("Continue")
            return value
        return wrapper

    def runCmd(self, *args, input:str=None) -> str:
        '''
        Execute the shell command sent by args. Returns and shows the result in
        the main window's output's text tab.

        args should be a series of strings with commas representing spaces, eg.
        'ls', '-A', '/home/'. The keyword input is the a string to feed to
        stdin after the command execution.
        '''
        try:
            p = subprocess.run(args, universal_newlines=True, input=input,
                               cwd=self.parent().dir_edit.text(),
                               timeout=float(self.parent().timeout_spinbox.value()),
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               check=True)
            self.parent().text.setPlainText(p.stdout)
            return p.stdout
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            # something went wrong executing the function. add the console
            # stdout to the end of the error string, then raise error again.
            if e.stdout:
                msg = (f'{e} At the moment of this error, the console output '
                       f'was:\n\n{e.stdout}')
            # TimeoutExpired and CalledProcessError do not have an attribute
            # for message, instead generating the message by overloading
            # __str__. workaround by just raising the base error type
            raise subprocess.SubprocessError(msg) from None
        except FileNotFoundError as e:
            # custom message
            e.strerror = 'The program cannot be found'
            e.filename = args[0]
            raise

    def readFloats(self, iterable:list, floats_per_line:int=None,
                   ignore_regex:re.Pattern|str=None, write_text:bool=False) -> None:
        '''
        Function that reads a file or list of strings that is formatted in a
        'grid', ie. in the form

        a1.1   a1.2   a1.3   ...   a1.n
        a2.1   a2.2   a2.3   ...   a2.n
        ...    ...    ...    ...   ...
        am.1   am.2   am.3   ...   am.n

        and stores floats found in it in an numpy array self.parent().data.
        Each cell should be in a numeric form that can be converted into a
        float like 0.123 or 1.234E-10, etc., and cells are seperated with any
        number of spaces (or tabs).

        iterable must be an iterable: if it is a string, use string.split('\n')
        before using this function.

        The function only adds a row to the final array if and only if there
        are `floats_per_line` floats in the line. If None, matches any number.

        If ignore_regex is set, the function ignores lines that match the
        regex.

        If write_text is True, writes the file or iterable into the 'Text'
        output tab self.parent().text.
        '''
        data = []
        if write_text:
            # clear text view if write_text is true
            self.parent().text.clear()
        for line in iterable:
            # write line to text view if write_text is true
            if write_text:
                self.parent().text.appendPlainText(line[:-1])
            # ignore finding floats on this line if matches regex
            if ignore_regex and re.search(ignore_regex, line):
                continue
            # should find this number of floats per line, if not, ignore
            # that line
            matches = re.findall(r'\S+', line)
            try:
                # regex returns strings, need to convert into float
                floats = list(map(float, matches))
            except ValueError:
                pass
            else:
                if (floats_per_line and len(matches) == floats_per_line)\
                or floats_per_line is None:
                    data.append(floats)
        if len(data) == 0:
            # nothing found
            raise ValueError('No floats found in iterable. Check console '
                             'output to see what went wrong?')
        self.parent().data = np.array(data)

    def writeTable(self, table:list, header:list=None, pre:str=None,
                   post:str=None) -> None:
        '''
        Function that writes a table (list of lists or tuples) into a formatted
        table written into self.parent().text.

        The function isn't able to format items which are not strings, floats,
        integers, or None very nicely. Strings should also be less than 16
        characters long.

        header is a list of column names which is shown above the table. pre
        and post are strings that are printed before and after the table,
        respectively.
        '''
        # obtain border length, the number of hyphens to section off
        if len(table) > 0:
            border_len = len(table[0])*17
        elif header:
            border_len = len(header)*17
        else:
            border_len = 0

        self.parent().text.clear()
        if pre:
            self.parent().text.appendPlainText(pre)
        self.parent().text.appendPlainText('-'*border_len)
        # print header, wrapped by hyphens
        if header:
            header = ''.join(['{:>16} '.format(col) for col in header])
            self.parent().text.appendPlainText(header)
            self.parent().text.appendPlainText('='*border_len)
        # print out results
        for row in table:
            out = ''
            for cell in row:
                if isinstance(cell, float) and np.isfinite(cell):
                    # scientific format with 9 dp (8 dp if |exponent| > 100)
                    if abs(cell) >= 1e+100 or 0 < abs(cell) <= 1e-100:
                        out += '{: .8e} '.format(cell)
                    else:
                        out += '{: .9e} '.format(cell)
                else:
                    # align right with width 16 (str() allows None to be formatted)
                    out += '{:>16} '.format(str(cell))
            self.parent().text.appendPlainText(out)
        # show bottom border only if there is at least one result
        if len(table) > 0:
            self.parent().text.appendPlainText('-'*border_len)
        if post:
            self.parent().text.appendPlainText(post)
