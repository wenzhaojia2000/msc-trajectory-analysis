# -*- coding: utf-8 -*-
'''
@author: 19081417

Consists of the single class that provides functionality for the 'Analyse
Convergence' tab of the analysis GUI. A class instance of this should be
included in the main UI class.
'''

import re
from PyQt5 import QtWidgets, QtCore
from pyqtgraph import intColor as colr
from ..ui.core import AnalysisTab

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
        methods = {
            0: self.ortho,  # check orthonormality of spfs
            1: self.rdgpop, # plot populations of grid edges
            2: self.natpop, # plot populations of natural orbitals
            3: self.qdq,    # plot coordinate expectation values
            4: self.norm    # plot time-evolution of norm of wavefunction
        }
        options = {
            0: 'ortho_box', 1: 'gpop_box', 2: 'natpop_box', 3: 'qdq_box'
        }
        required_files = {
            0: ['psi'], 1: ['gridpop'],  2: ['check'], 3: ['check'],
            4: ['psi']
        }

        super()._activate(
            push_name='analconv_push', radio_box_name='analconv_radio',
            methods=methods, options=options, required_files=required_files
        )

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
        # group box 'coordinate expectation options'
        self.qdq_dof = self.findChild(QtWidgets.QSpinBox, 'qdq_dof')
        self.qdq_state = self.findChild(QtWidgets.QSpinBox, 'qdq_state')

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
        match = re.findall(r'#.*?\n(.*)#', output, flags=re.DOTALL)
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
            self.window().graph.plot(arr[:, 0], arr[:, 2+i], name=f'Mode {i}',
                                     pen=colr(i-1, n_modes, maxValue=200))

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

        t.1    s1.1    s2.1    ...    sn.1
        t.2    s1.2    s2.2    ...    sn.2
        ...    ...     ...     ...    ...
        t.m    s1.m    s2.m    ...    sn.m

        where t is time and sn is the natural population for SPF n.

        Plots the populations of natural orbitals against time.
        '''
        # additional arguments for natpop
        natpop_options = [
            str(self.natpop_mode.value()),
            str(self.natpop_state.value())
        ]
        self.runCmd('rdcheck', 'natpop', *natpop_options)

        # find filename of command output
        filepath = self.window().cwd/f'natpop_{"_".join(natpop_options)}.pl'
        # assemble data matrix
        with open(filepath, mode='r', encoding='utf-8') as f:
            self.window().data = self.readFloats(f)

        # start plotting
        self.window().graph.reset(switch_to_plot=True)
        self.window().graph.setLabels(title='Natural population',
                                      bottom='Time (fs)', left='Weight')
        n_spfs = self.window().data.shape[1] - 1 # minus time column
        for i in range(1, n_spfs + 1):
            self.window().graph.plot(self.window().data[:, 0], self.window().data[:, i],
                                     name=f'SPF {i}', pen=colr(i-1, n_spfs, maxValue=200))

    def qdq(self):
        '''
        Reads the file output of using rdcheck qdq, which is expected to be
        in the format, where each cell is a float,

        t.1    q.1    dq.1
        t.2    q.2    dq.2
        ...    ...    ...
        t.m    q.m    dq.m

        where t is time, q is the expectation of the coordinate value <q> and
        dq is the width of the <q>, <dq>.

        Plots <q> and <dq> against time.
        '''
        # additional arguments for qdq
        qdq_options = [
            str(self.qdq_dof.value()),
            str(self.qdq_state.value())
        ]
        self.runCmd('rdcheck', 'qdq', *qdq_options)

        # find filename of command output
        filepath = self.window().cwd/f'qdq_{"_".join(qdq_options)}.pl'
        # assemble data matrix
        with open(filepath, mode='r', encoding='utf-8') as f:
            self.window().data = self.readFloats(f, 3)

        # start plotting
        self.window().graph.reset(switch_to_plot=True)
        self.window().graph.setLabels(title='Coordinate expectation values',
                                      bottom='Time (fs)',
                                      left=f'DOF {self.qdq_dof.value()}')
        self.window().graph.plot(self.window().data[:, 0], self.window().data[:, 1],
                                 name='q', pen='r')
        self.window().graph.plot(self.window().data[:, 0], self.window().data[:, 2],
                                 name='dq', pen='b')

    def norm(self):
        '''
        Not implemented as the corresponding quantics analysis program is
        currently broken.
        '''
        raise NotImplementedError
