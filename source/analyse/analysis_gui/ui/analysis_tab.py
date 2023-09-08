# -*- coding: utf-8 -*-
'''
@author: 19081417

Consists of the abstract class for the analysis tabs in the main UI.
'''

from shlex import split as shsplit
import re
import subprocess
import sys
import traceback

import numpy as np
from PyQt5 import QtWidgets, QtCore, uic

class AnalysisTab(QtWidgets.QWidget):
    '''
    Abstract class of an analysis tab. The tab should be a promoted QWidget
    which is a child of the main window's toolbar. The tab should have the
    following widgets in its .ui file:

    - One QWidget container named 'list_widget', containing at least one radio
      button. This represents a list of analysis choices.
    - One QPushButton named 'analyse' that when pushed calls a method of choice
      depending on the what radio button is selected.

    Also consists of a couple convenience functions which may aid with writing
    analysis functions.
    '''

    def __init__(self, ui_file:str, *args, **kwargs):
        '''
        Constructor method that loads the UI file. Also see self._activate,
        which is similar to __init__ but is delayed until manually called.
        '''
        super().__init__(*args, **kwargs)
        uic.loadUi(ui_file, self)

    def activate(self, methods:dict, options:dict, required_files:dict):
        '''
        Automatically sets up the low level functionality of the Analysis
        widget, including what method to call depending on what radio button
        is selected, etc.

        The functionality requires a pointer to the AnalysisMain window using
        self.window(). This is not available after everything else has loaded,
        so this can't be called in self.__init__(). Instead, call this at the
        end of AnalysisMain.__init__().

        The dictionary parameters all have the radio button index (int) as the
        key, **in the order shown in Qt Designer**. For the value:
            - methods has the method to call when the corresponding radio
              button is selected and 'Analyse' is pushed. There must be one
              method for each radio button.
            - `options` has the name of the QGroupBox to show which allow
              the user to select further options when a radio button is
              selected.
            - `required_files` has a *list* of filenames that are required
              for the method. If they are not found, the 'Analyse' button is
              disabled (with text giving the missing file(s)).
        '''
        self.methods = methods
        self.options = options
        self.required_files = required_files
        # list of the radio buttons inside the list widget
        self.radio = self.list_widget.findChildren(QtWidgets.QRadioButton)
        if len(self.radio) != len(self.methods):
            raise ValueError('There must be a corresponding method for each '
                             'radio button.')

        # connect objects
        self.analyse.clicked.connect(self.analysePushed)
        # show the update options box when certain result is selected
        for radio in self.radio:
            radio.clicked.connect(self.optionSelected)
        # refresh options if directory/options menu item has changed
        self.window().dir.edit.textChanged.connect(self.optionSelected)
        self.window().allow_add_flags.triggered.connect(self.optionSelected)
        self.window().no_command.triggered.connect(self.optionSelected)

        # should automatically hide the boxes that correspond to an option
        # that isn't selected
        self.optionSelected()
        # check the file exists for the initially checked radio box (index 0)
        self.checkFileExists(0)

    @QtCore.pyqtSlot()
    def optionSelected(self):
        '''
        Shows per-analysis options in a QGroupBox if a valid option is checked,
        with the options dictionary given in self.activate. Can be overriden if
        certain options are generated on-demand, using `super().optionSelected()`.
        '''
        # need to iterate over all radio boxes rather than just the one selected
        # since options box needs to be hidden for radio boxes NOT selected
        for index, radio in enumerate(self.radio):
            if radio.isChecked():
                # check file associated with radio button exists
                self.checkFileExists(index)
                if index in self.options:
                    self.options[index].show()
            elif index in self.options:
                self.options[index].hide()

    @QtCore.pyqtSlot()
    def analysePushed(self):
        '''
        Action to perform when the tab's analyse button is pushed, which is to
        call the associated method given in self.methods.
        '''
        # get index of checked radio button (there should only be 1)
        radio_index = [index for index, radio in enumerate(self.radio)
                       if radio.isChecked()][0]
        # set cursor to wait cursor
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        # freeze push button until method is executed
        self.analyse.setEnabled(False)
        self.analyse.setText('Busy')
        # force pyqt to update button immediately (otherwise pyqt leaves
        # this until the next event loop and nothing happens)
        self.analyse.repaint()
        try:
            # call method associated with index
            self.methods[radio_index]()
        except Exception as e:
            # any exceptions raised by the method would not allow continue to
            # be restored, softlocking the program -- need to catch all
            # exceptions. print the full traceback to stderr for developer,
            # show an error message for the user
            print(traceback.format_exc(), file=sys.stderr)
            # switch to text tab to see if there are any other explanatory errors
            self.window().tab_widget.setCurrentIndex(0)
            QtWidgets.QMessageBox.critical(self.window(), 'Error', f'{type(e).__name__}: {e}')
        # method executed, now can unfreeze
        QtWidgets.QApplication.restoreOverrideCursor()
        self.analyse.setEnabled(True)
        self.analyse.setText('Analyse')

    def checkFileExists(self, index:int):
        '''
        Disables the 'Analyse' button from being clicked if the filename
        associated with the analysis command (self.required_files) is not found.

        This functionality is disabled if the user has checked the 'Allow
        additional flags' or the 'No command mode' options.
        '''
        ignore = (self.window().allow_add_flags.isChecked() or
                  self.window().no_command.isChecked() or
                  index not in self.required_files)
        # enable push button if additional flags are enabled, no command mode
        # is one or no specified required files for this index
        if ignore:
            self.analyse.setEnabled(True)
            self.analyse.setText('Analyse')
            return None

        # need to generate path objects every time this is called rather than
        # only once in self._activate since self.window().dir.cwd is not fixed
        filenames = [self.window().dir.cwd/file for file in self.required_files[index]]
        missing_files = [file.name for file in filenames if not file.is_file()]
        if missing_files:
            self.analyse.setEnabled(False)
            self.analyse.setText('Missing: ' + ', '.join(missing_files))
        else:
            self.analyse.setEnabled(True)
            self.analyse.setText('Analyse')
        return None

    ##### convenience functions #####

    @staticmethod
    def readFloats(iterable:list, floats_per_line:int=None,
                   ignore_regex:re.Pattern|str=None) -> np.ndarray:
        '''
        Function that reads a file or list of strings that is formatted in a
        'grid', ie. in the form

        a1.1   a1.2   a1.3   ...   a1.n
        a2.1   a2.2   a2.3   ...   a2.n
        ...    ...    ...    ...   ...
        am.1   am.2   am.3   ...   am.n

        then returns floats found in it.

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
        '''
        data = []
        for line in iterable:
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
                if (floats_per_line and len(floats) == floats_per_line)\
                or (floats_per_line is None and len(floats) > 0):
                    data.append(floats)
        if len(data) == 0:
            # nothing found
            raise ValueError('No floats found in iterable. Check console '
                             'output to see what went wrong?')
        return np.array(data)

    def runCmd(self, *args, input:str=None) -> str:
        '''
        Execute the shell command sent by args. Returns and shows the result in
        the main window's output's text tab.

        args should be a series of strings with commas representing spaces, eg.
        'ls', '-A', '/home/'. The keyword input is the a string to feed to
        stdin after the command execution.
        '''
        # change from tuple to list
        args = list(args)
        if self.window().no_command.isChecked():
            # don't do anything if user has set no command mode
            return None
        if self.window().allow_add_flags.isChecked():
            # add additional flags set by the user
            # note: if the original command contains positional arguments
            # appending the extra flags at the end may not work, since the
            # analysis program stops reading input at that point. instead,
            # insert just after the name of the program called.
            # workaround fails if the flags generated by the gui overwrite the
            # additional flags or cause an error -- may need to integrate this
            # extra flag into the gui if this is the case.
            args[1:1] = shsplit(self.window().add_flags.text())

        try:
            p = subprocess.run(args, universal_newlines=True, input=input,
                               cwd=self.window().dir.cwd, check=True,
                               timeout=self.window().timeout.value(),
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
