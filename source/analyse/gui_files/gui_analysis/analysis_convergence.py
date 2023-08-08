# -*- coding: utf-8 -*-
'''
@author: 19081417

Consists of the single class that provides functionality for the 'Analyse
Convergence' tab of the analysis GUI. A class instance of this should be
included in the main UI class.
'''

from pathlib import Path
from PyQt5 import QtWidgets, QtCore
from .ui_base import AnalysisTab

class AnalysisConvergence(AnalysisTab):
    '''
    Promoted widget that defines functionality for the "Analyse Convergence"
    tab of the analysis GUI.
    '''
    def _activate(self):
        '''
        Activation method. See the documentation in AnalysisTab for more
        information.
        '''
        super()._activate(push_name='analconv_push', layout_name='analconv_layout',
                          options={
                              1: 'gpop_box'
                          })

    def findObjects(self, push_name:str, box_name:str):
        '''
        Obtains UI elements as instance variables, and possibly some of their
        properties.
        '''
        super().findObjects(push_name, box_name)
        # group box 'grid population options'
        self.gpop_nz = self.findChild(QtWidgets.QSpinBox, 'gpop_nz')
        self.gpop_dof = self.findChild(QtWidgets.QSpinBox, 'gpop_dof')

    @QtCore.pyqtSlot()
    @AnalysisTab.freezeContinue
    def continuePushed(self):
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
            self.window().tab_widget.setCurrentIndex(0)
            QtWidgets.QMessageBox.critical(self.window(), 'Error', f'{type(e).__name__}: {e}')

    def rdgpop(self):
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

        filepath = Path(self.window().dir_edit.text())/'gpop.pl'
        # assemble data matrix
        with open(filepath, mode='r', encoding='utf-8') as f:
            self.readFloats(f, 5, r'^#')

        # start plotting
        self.window().resetPlot(True)
        self.window().setPlotLabels(title='Grid edge population',
                                    bottom='Time (fs)', left='Population')
        self.window().graph.plot(self.window().data[:, 0], self.window().data[:, 1],
                                 name='Grid (begin)', pen='r')
        self.window().graph.plot(self.window().data[:, 0], self.window().data[:, 2],
                                 name='Grid (end)',
                                 pen={'color': 'r', 'style': QtCore.Qt.DashLine})
        self.window().graph.plot(self.window().data[:, 0], self.window().data[:, 3],
                                 name='Basis (begin)', pen='b')
        self.window().graph.plot(self.window().data[:, 0], self.window().data[:, 4],
                                 name='Basis (end)',
                                 pen={'color': 'b', 'style': QtCore.Qt.DashLine})
