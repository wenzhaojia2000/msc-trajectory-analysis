# -*- coding: utf-8 -*-
'''
@author: 19081417

Consists of the single class that provides functionality for the 'Analyse
Convergence' tab of the analysis GUI. A class instance of this should be
included in the main UI class.
'''

import re
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
                              0: 'ortho_box', 1: 'gpop_box', 2: 'natpop_box'
                          })

    def findObjects(self, push_name:str, box_name:str):
        '''
        Obtains UI elements as instance variables, and possibly some of their
        properties.
        '''
        super().findObjects(push_name, box_name)
        # group box 'orthonormality options'
        self.ortho_state = self.findChild(QtWidgets.QSpinBox, 'ortho_state')
        # group box 'grid population options'
        self.gpop_nz = self.findChild(QtWidgets.QSpinBox, 'gpop_nz')
        self.gpop_dof = self.findChild(QtWidgets.QSpinBox, 'gpop_dof')
        # group box 'natural population options'
        self.natpop_mode = self.findChild(QtWidgets.QSpinBox, 'natpop_mode')
        self.natpop_state = self.findChild(QtWidgets.QSpinBox, 'natpop_state')

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
                case 'analconv_1': # check orthonormality of spfs
                    self.ortho()
                case 'analconv_2': # plot populations of grid edges
                    self.rdgpop()
                case 'analconv_3': # plot populations of natural orbitals
                    self.natpop()
                case 'analconv_4': # plot coordinate expectation values
                    self.runCmd('rdcheck', 'qdq', '1', '1')
                case 'analconv_5': # plot time-evolution of norm of wavefunction
                    raise NotImplementedError
        except Exception as e:
            # switch to text tab to see if there are any other explanatory errors
            self.window().tab_widget.setCurrentIndex(0)
            QtWidgets.QMessageBox.critical(self.window(), 'Error', f'{type(e).__name__}: {e}')

    def ortho(self):
        '''
        Reads the command output of using ortho, which is expected to be in
        the format, where each cell is a float,

        [directory and mode information]
        # Time[fs]  state  total   mode( 1) ...   mode( n)
          t.1       sA     tot.A1  o.A1     ...   o.An
          t.1       sB     tot.B1  o.B1     ...   o.Bn
          ...       ...    ...     ...      ...   ...
          t.1       sX     tot.X1  o.X1     ...   o.Xn

          t.2       sA     tot.A2  o.A2     ...   o.An
          ...       ...    ...     ...      ...   ...
          t.m       sX     tot.Xm  o.Xm     ...   o.Xm
        # Time[fs]  state  total   mode( 1) ... mode( n)

        where t is time, sA, sB, ... sX are the states, 1 ... n are the modes,
        and o is the orthonormality error for that state and mode.

        Plots the orthonormality error for each mode for a given state.
        '''
        output = self.runCmd('ortho')
        # get the relevant data we want (between the two #, but skip first line
        # which is the header - see docstring)
        match = re.findall(r'(?<=#).*?\n(.*)(?=#)', output, flags=re.DOTALL)
        if len(match) != 1:
            raise ValueError('Invalid ortho output?')
        # assemble data matrix
        self.window().data = self.readFloats(match[0].split('\n'))

        # only select rows where state column equals user selected state, using
        # a numpy mask
        state = self.ortho_state.value()
        arr = self.window().data[self.window().data[:, 1] == state, :]
        if arr.size == 0:
            max_state = self.window().data[:, 1].max()
            raise ValueError(f'Selected state {state} is larger than highest '
                             f'state {int(max_state)}')
        # number of modes is number of columns minus time, state, total columns
        n_modes = self.window().data.shape[1] - 3
        # start plotting
        self.window().graph.reset(switch_to_plot=True)
        self.window().graph.setLabels(title='SPF Orthonormality',
                                      bottom='Time (fs)', left='Orthonormality error')
        self.window().graph.plot(arr[:, 0], arr[:, 2], name='Total', pen='k')
        for i in range(1, n_modes+1):
            self.window().graph.plot(arr[:, 0], arr[:, 2+i],
                                     name=f'Mode {i}', pen=(i-1, n_modes))

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

        filepath = self.window().cwd/'gpop.pl'
        # assemble data matrix
        with open(filepath, mode='r', encoding='utf-8') as f:
            self.window().data = self.readFloats(f, 5, ignore_regex=r'^#')

        # start plotting
        self.window().graph.reset(switch_to_plot=True)
        self.window().graph.setLabels(title='Grid edge population',
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

    def natpop(self):
        '''
        Reads the file output of using rdcheck natpop, which is expected to be
        in the format, where each cell is a float,

        t.1    x.1
        t.2    x.2
        ...    ...
        t.m    x.m

        where t is time and x is the natural population.

        Plots the populations of natural orbitals.
        '''
        # additional arguments for rdgpop
        natpop_options = [
            str(self.natpop_mode.value()),
            str(self.natpop_state.value())
        ]
        self.runCmd('rdcheck', 'natpop', *natpop_options)

        # find filename of command output
        filepath = self.window().cwd/f'natpop_{"_".join(natpop_options)}.pl'
        # assemble data matrix
        with open(filepath, mode='r', encoding='utf-8') as f:
            self.window().data = self.readFloats(f, 2)

        # start plotting
        self.window().graph.reset(switch_to_plot=True)
        self.window().graph.setLabels(title='Natural population',
                                      bottom='Time (fs)', left='Weight')
        self.window().graph.plot(self.window().data[:, 0], self.window().data[:, 1],
                                 name='Population', pen='r')
