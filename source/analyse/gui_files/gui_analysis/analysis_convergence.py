# -*- coding: utf-8 -*-
'''
@author: 19081417

Consists of the single class that provides functionality for the 'Analyse
Convergence' tab of the analysis GUI. A class instance of this should be
included in the main UI class.
'''

from pathlib import Path
from PyQt5 import QtWidgets, QtCore
from .ui_base import AnalysisMainInterface, AnalysisTab

class AnalysisConvergence(AnalysisTab):
    '''
    Defines functionality for the "Analyse Convergence" tab of the analysis
    GUI.
    '''
    def __init__(self, parent:AnalysisMainInterface) -> None:
        '''
        Initiation method.
        '''
        super().__init__(parent=parent, push_name='analconv_push',
                         box_name='analconv_layout')

    def findObjects(self, push_name, box_name) -> None:
        '''
        Obtains UI elements as instance variables, and possibly some of their
        properties.
        '''
        super().findObjects(push_name, box_name)
        # group box 'grid population options'
        self.gpop_box = self.parent().findChild(QtWidgets.QGroupBox, 'gpop_box')
        self.gpop_nz = self.parent().findChild(QtWidgets.QSpinBox, 'gpop_nz')
        self.gpop_dof = self.parent().findChild(QtWidgets.QSpinBox, 'gpop_dof')
        # box is hidden initially
        self.gpop_box.hide()

    def connectObjects(self) -> None:
        '''
        Connects UI elements so they do stuff when interacted with.
        '''
        super().connectObjects()
        # show the autocorrelation box when certain result in analyse results
        for radio in self.radio:
            radio.clicked.connect(self.optionSelected)

    @QtCore.pyqtSlot()
    def optionSelected(self) -> None:
        '''
        Shows per-analysis options if a valid option is checked.
        '''
        options = {1: self.gpop_box}
        for radio, box in options.items():
            if self.radio[radio].isChecked():
                box.show()
            else:
                box.hide()

    @QtCore.pyqtSlot()
    @AnalysisTab.freezeContinue
    def continuePushed(self) -> None:
        '''
        Action to perform when the tab's 'Continue' button is pushed.
        '''
        # get objectName() of checked radio button (there should only be 1)
        radio_name = [radio.objectName() for radio in self.radio
                      if radio.isChecked()][0]
        try:
            match radio_name:
                case 'analconv_1': # check orthonormality of spfs in psi file
                    self.runCmd('ortho')
                case 'analconv_2': # plot populations of grid edges
                    self.rdgpop()
                case 'analconv_3': # plot populations of states
                    self.runCmd('rdcheck', 'spop')
                case 'analconv_4': # plot populations of natural orbitals
                    self.runCmd('rdcheck', 'natpop', '1', '1')
                case 'analconv_5': # plot coordinate expectation values
                    self.runCmd('rdcheck', 'qdq', '1', '1')
                case 'analconv_6': # plot time-evolution of norm of wavefunction
                    self.runCmd('norm')
        except Exception as e:
            # switch to text tab to see if there are any other explanatory errors
            self.parent().tab_widget.setCurrentIndex(0)
            QtWidgets.QMessageBox.critical(self.parent(), 'Error', f'{type(e).__name__}: {e}')

    def rdgpop(self) -> None:
        '''
        Reads the file output of using rdgpop, which is expected to be in
        the format, where each cell is a float,

        t.1    gb.1    ge.1    bb.1   be.1
        t.2    gb.2    ge.2    bb.2   be.2
        ...    ...     ...     ...    ...
        t.m    gb.m    ge.m    bb.m   be.m

        where t is time, gb and ge are the beginning and end of the spacial
        grids, and bb and be are the beginning and end of the basis occupations.
        Lines starting with '#' are ignored.

        Plots the populations of grid edges.
        '''
        # additional arguments for rdgpop
        gpop_options = [
            str(self.gpop_nz.value()),
            str(self.gpop_dof.value())
        ]
        self.runCmd('rdgpop', '-w', *gpop_options)

        filepath = Path(self.parent().dir_edit.text())/'gpop.pl'
        # assemble data matrix
        with open(filepath, mode='r', encoding='utf-8') as f:
            self.readFloats(f, 5, r'^#')
        if self.parent().keep_files.isChecked() is False:
            # delete intermediate file
            filepath.unlink()

        # start plotting
        self.parent().resetPlot(True)
        self.parent().setPlotLabels(title='Grid edge population',
                                    bottom='Time (fs)', left='Population')
        self.parent().graph.plot(self.parent().data[:, 0], self.parent().data[:, 1],
                                 name='Grid (begin)', pen='r')
        self.parent().graph.plot(self.parent().data[:, 0], self.parent().data[:, 2],
                                 name='Grid (end)',
                                 pen={'color': 'r', 'style': QtCore.Qt.DashLine})
        self.parent().graph.plot(self.parent().data[:, 0], self.parent().data[:, 3],
                                 name='Basis (begin)', pen='b')
        self.parent().graph.plot(self.parent().data[:, 0], self.parent().data[:, 4],
                                 name='Basis (end)',
                                 pen={'color': 'b', 'style': QtCore.Qt.DashLine})
