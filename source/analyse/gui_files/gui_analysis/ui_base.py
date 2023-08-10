# -*- coding: utf-8 -*-
'''
@author: 19081417

Consists of the abstract class for the analysis tabs in the main UI, as well
as the superclass which the main UI and UI tabs extend from.
'''

from abc import ABC, ABCMeta, abstractmethod
from functools import wraps
from typing import Callable
import re
import subprocess
import numpy as np

from PyQt5 import QtWidgets, QtCore

class AnalysisMeta(type(QtCore.QObject), ABCMeta):
    '''
    Allows the AnalysisBase class to extend from ABC's metaclass so multiple
    inheritance from a Qt object and an abstract class doesn't cause metaclass
    conflict.
    '''

class AnalysisBase(ABC):
    '''
    Abstract class of an analysis GUI, of some kind.
    '''
    @abstractmethod
    def findObjects(self):
        '''
        Obtains UI elements as instance variables, and possibly some of their
        properties.
        '''
        # abstractmethod will automatically raise an error if method is not
        # implemented so seperate raise NotImplementedError is redundant

    @abstractmethod
    def connectObjects(self):
        '''
        Connects UI elements so they do stuff when interacted with.
        '''

class AnalysisTab(AnalysisBase, QtWidgets.QWidget, metaclass=AnalysisMeta):
    '''
    Abstract class of an analysis tab. The tab should be a promoted QWidget
    which is a child of the main window's toolbar. The tab should have the
    following:

    - One QBoxLayout instance, containing at least one radio button
          (Recommend QVBoxLayout)
    - One QPushButton instance (confirming radio button selection)

    Also consists of convenience functions which may aid with writing analysis
    functions.
    '''

    def _activate(self, push_name:str, layout_name:str, options:dict={},
                  *args, **kwargs):
        '''
        Activation method. This method is similar to __init__, but for promoted
        widgets, the initialiser is called before any of its children are
        added, and as such, self.findChild fails to find anything. Instead,
        call when everything is loaded, ie. in the class for AnalysisMain to
        add functionality to the analysis tab.

        Requires the object name of its QPushButton and QBoxLayout instances
        as mentioned in the class docstring.

        May optionally give an options dictionary, which allows the user to
        select further options when a radio button is selected. The dictionary
        has key: radio button index (int) and value: name of the QGroupBox to
        show when that button is selected.
        '''
        # for speed, turn box names into the objects themselves
        for index, box_name in options.items():
            options[index] = self.findChild(QtWidgets.QGroupBox, box_name)
            if options[index] is None:
                raise ValueError(f'QGroupBox with name {box_name} was not found')
        self.options = options

        self.findObjects(push_name, layout_name)
        self.connectObjects()
        # should automatically hide the boxes that correspond to an option
        # that isn't selected
        self.optionSelected()

    def findObjects(self, push_name:str, layout_name:str):
        '''
        A possibly incomplete implementation of the findObjects method. Any
        derived class can add further implementation to this method by using
        `super().findObjects(push_name, box_name)`.
        '''
        self.push = self.findChild(QtWidgets.QPushButton, push_name)
        if self.push is None:
            raise ValueError(f'QPushButton with name {push_name} was not found')
        layout = self.findChild(QtWidgets.QBoxLayout, layout_name)
        if layout is None:
            raise ValueError(f'QBoxLayout with name {layout_name} was not found')
        self.radio = [layout.itemAt(i).widget() for i in range(layout.count())]

    def connectObjects(self):
        '''
        A possibly incomplete implementation of the connectObjects method. Any
        derived class can add further implementation to this method by using
        `super().connectObjects()`.
        '''
        self.push.clicked.connect(self.continuePushed)
        # show the update options box when certain result is selected
        for radio in self.radio:
            radio.clicked.connect(self.optionSelected)
        # refresh options if directory has changed
        self.window().dir_edit.textChanged.connect(self.optionSelected)

    @QtCore.pyqtSlot()
    def optionSelected(self):
        '''
        Shows per-analysis options in a QGroupBox if a valid option is checked,
        with the options dictionary given in __init__. Can be overriden if
        certain options are generated on-demand, using `super().optionSelected()`.
        '''
        for index, box in self.options.items():
            if self.radio[index].isChecked():
                box.show()
            else:
                box.hide()

    @abstractmethod
    @QtCore.pyqtSlot()
    def continuePushed(self):
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

    def readFloats(self, iterable:list, floats_per_line:int=None,
                   ignore_regex:re.Pattern|str=None, write_text:bool=False):
        '''
        Function that reads a file or list of strings that is formatted in a
        'grid', ie. in the form

        a1.1   a1.2   a1.3   ...   a1.n
        a2.1   a2.2   a2.3   ...   a2.n
        ...    ...    ...    ...   ...
        am.1   am.2   am.3   ...   am.n

        and stores floats found in it in an numpy array self.window().data.
        Each cell should be in a numeric form that can be converted into a
        float like 0.123 or 1.234E-10, etc., and cells are seperated with any
        number of spaces (or tabs).

        iterable must be an iterable: if it is a string, use string.split('\n')
        before using this function.

        The function only adds a row to the final array if and only if there
        are `floats_per_line` floats in the line. If None, matches any number
        greater than zero.

        If ignore_regex is set, the function ignores lines that match the
        regex.

        If write_text is True, writes the file or iterable into the 'Text'
        output tab self.window().text.
        '''
        data = []
        if write_text:
            # clear text view if write_text is true
            self.window().text.clear()
        for line in iterable:
            # write line to text view if write_text is true
            if write_text:
                self.window().text.appendPlainText(line[:-1])
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
                or (floats_per_line is None and len(matches) > 0):
                    data.append(floats)
        if len(data) == 0:
            # nothing found
            raise ValueError('No floats found in iterable. Check console '
                             'output to see what went wrong?')
        self.window().data = np.array(data)

    def runCmd(self, *args, input:str=None) -> str:
        '''
        Execute the shell command sent by args. Returns and shows the result in
        the main window's output's text tab.

        args should be a series of strings with commas representing spaces, eg.
        'ls', '-A', '/home/'. The keyword input is the a string to feed to
        stdin after the command execution.
        '''
        if self.window().no_command.isChecked():
            return None
        try:
            p = subprocess.run(args, universal_newlines=True, input=input,
                               cwd=self.window().cwd, check=True,
                               timeout=self.window().timeout_spinbox.value(),
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            self.window().text.setPlainText(p.stdout)
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

    def getModes(self) -> list:
        '''
        Returns a list of mode names from the input file in the current
        directory.
        '''
        with open(self.window().cwd/'input', mode='r', encoding='utf-8') as f:
            txt = f.read()
            # find modes in SPF-BASIS-SECTION
            spf_section = re.findall(r'SPF-BASIS-SECTION\n(.*)\nend-spf-basis-section',
                                     txt, re.DOTALL)
            # if section does not exist, might be direct dynamics. find in
            # nmode subsection in INITIAL-GEOMETRY-SECTION
            ddmode_section = re.findall(r'nmode\n(.*)\nend-nmode', txt, re.DOTALL)
            if spf_section:
                # a list of modes are displayed before an = sign. match all of
                # them, split by comma, then remove surrounding whitespace
                modes = [mode.strip() for line in re.findall(r'.+(?==)', spf_section[0])\
                                      for mode in line.split(',')]
            elif ddmode_section:
                # a list of modes are the first entry in each line (assuming
                # mode names can't have whitespace in them).
                modes = re.findall(r'^\s*\S+', ddmode_section[0], re.MULTILINE)
            else:
                raise ValueError('Cannot find modes in input file')
        return modes
