# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

import re
import numpy as np
from PyQt5 import QtWidgets, QtCore
from .ui_base import AnalysisMainInterface, AnalysisTab

class AnalysisIntegrator(QtWidgets.QWidget, AnalysisTab):
    '''
    Defines functionality for the "Analyse Integrator" tab of the analysis
    GUI.
    '''
    def __init__(self, owner:AnalysisMainInterface) -> None:
        '''
        Initiation method.
        '''
        super().__init__(owner=owner, push_name='analint_push',
                         box_name='analint_layout')
    
    def findObjects(self, push_name, box_name) -> None:
        '''
        Obtains UI elements as instance variables, and possibly some of their
        properties.
        '''
        super().findObjects(push_name, box_name)
        self.update_box = self.owner.findChild(QtWidgets.QGroupBox, 'update_box')
        self.update_plot = self.owner.findChild(QtWidgets.QComboBox, 'update_combobox')
        # box is hidden initially
        self.update_box.hide()

    def connectObjects(self) -> None:
        '''
        Connects UI elements so they do stuff when interacted with.
        '''
        super().connectObjects()
        # show the update options box when certain result is selected
        for radio in self.radio:
            radio.clicked.connect(self.updateOptionSelected)

    @QtCore.pyqtSlot()
    @AnalysisTab.freezeContinue
    def continuePushed(self) -> None:
        '''
        Action to perform when the tab's 'Continue' button is pushed.
        '''
        # get objectName() of checked radio button (there should only be 1)
        radio_name = [radio.objectName() for radio in self.radio
                      if radio.isChecked()][0]
        match radio_name:
            case 'analint_1': # analyse step size
                self.runCmd('rdsteps')
            case 'analint_2': # look at timing file
                self.runCmd('cat', './timing')
            case 'analint_3': # plot update file step size
                self.rdupdate(plot_error=False)
            case 'analint_4': # plot update file errors
                self.rdupdate(plot_error=True)

    @QtCore.pyqtSlot()
    def updateOptionSelected(self) -> None:
        '''
        Shows the update options if a valid option is checked.
        '''
        if self.radio[3].isChecked():
            self.update_box.show()
        else:
            self.update_box.hide()

    def rdupdate(self, plot_error:bool=False) -> None:
        '''
        Reads the command output of using rdupdate, which is expected to be in
        the format

        x.1    y1.1    y2.1    y3.1
        x.2    y1.2    y2.2    y3.2
        ...    ...     ...     ...
        x.m    y1.m    y2.m    y3.m

        where x is time, y1 is step size, y2 is error of A, y3 is error of phi.
        Each cell should be in a numeric form that can be converted into a 
        float like 0.123 or 1.234E-10, etc., and cells are seperated with any
        number of spaces (or tabs).

        Plots the step size is plot_error is false, otherwise plots the errors,
        chosen by the self.update_plot combobox.
        '''
        output = self.runCmd('rdupdate')
        if output is None:
            return None
        # assemble data matrix
        arr = []
        for line in output.split('\n'):
            # find all floats in the line
            matches = re.findall(self.float_regex, line)
            # should find four floats per line (x, y1, y2, y3)
            if len(matches) == 4:
                # regex returns strings, need to convert into float
                arr.append(list(map(float, matches)))
        self.owner.data = np.array(arr)
        if self.owner.data.size == 0:
            # nothing found: output is likely something else eg. some text
            # like "cannot open or read update file". in which case, don't
            # plot anything
            print('[AnalysisIntegrator.rdupdate] I wasn\'t given any values to plot')
            return None

        # clear plot and switch tab to show plot
        self.owner.graph.clear()
        self.owner.graph.getPlotItem().enableAutoRange()
        self.owner.tab_widget.setCurrentIndex(1)
        self.owner.slider.hide()

        # start plotting, depending on options
        self.owner.graph.setLabel('bottom', 'Time (fs)', color='k')
        self.owner.toggleLegend()
        if plot_error:
            self.owner.graph.setLabel('left', 'Error', color='k')
            self.owner.changePlotTitle('Update file errors')
            match self.update_plot.currentIndex():
                case 0:
                    self.owner.graph.plot(self.owner.data[:, 0], self.owner.data[:, 2],
                                          name='Error of A-vector', pen='r')
                    self.owner.graph.plot(self.owner.data[:, 0], self.owner.data[:, 3],
                                          name='Error of SPFs', pen='b')
                case 1:
                    self.owner.graph.plot(self.owner.data[:, 0], self.owner.data[:, 2],
                                          name='Error of A-vector', pen='r')
                case 2:
                    self.owner.graph.plot(self.owner.data[:, 0], self.owner.data[:, 3],
                                          name='Error of SPFs', pen='b')
        else:
            self.owner.changePlotTitle('Update file step size')
            self.owner.graph.setLabel('left', 'Step size (fs)', color='k')
            self.owner.graph.plot(self.owner.data[:, 0], self.owner.data[:, 1],
                                  name='Step size', pen='r')
        return None
