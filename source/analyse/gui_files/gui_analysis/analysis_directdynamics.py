# -*- coding: utf-8 -*-
'''
@author: 19081417

Consists of the single class that provides functionality for the 'Analyse
Direct Dynamics' tab of the analysis GUI. A class instance of this should be
included in the main UI class.
'''

import re
import sqlite3
import numpy as np
from PyQt5 import QtWidgets, QtCore
from .ui_base import AnalysisTab

class AnalysisDirectDynamics(AnalysisTab):
    '''
    Promoted widget that defines functionality for the 'Analyse Direct
    Dynamics' tab of the analysis GUI.
    '''
    def _activate(self):
        '''
        Activation method. See the documentation in AnalysisTab for more
        information.
        '''
        super()._activate(push_name='analdd_push', layout_name='analdd_layout',
                          options={
                              1: 'gwptraj_box', 2: 'findpes_box',
                              3: 'clean_box', 4: 'sql_box'
                          })
        # one of the boxes inside findpes should be hidden
        self.findpesOptionChanged()

    def findObjects(self, push_name:str, box_name:str):
        '''
        Obtains UI elements as instance variables, and possibly some of their
        properties.
        '''
        super().findObjects(push_name, box_name)
        # group box 'gwp trajectory options'
        self.gwptraj_task = self.findChild(QtWidgets.QComboBox, 'gwptraj_task')
        self.gwptraj_mode = self.findChild(QtWidgets.QSpinBox, 'gwptraj_mode')
        # group box 'pes/apes options'
        self.findpes_type = self.findChild(QtWidgets.QComboBox, 'findpes_type')
        self.findpes_task = [
            self.findChild(QtWidgets.QRadioButton, 'findpes_int'),
            self.findChild(QtWidgets.QRadioButton, 'findpes_mat')
        ]
        self.findpes_int_box = self.findChild(QtWidgets.QFrame, 'findpes_int_box')
        self.findpes_mat_box = self.findChild(QtWidgets.QFrame, 'findpes_mat_box')
        self.findpes_emin = self.findChild(QtWidgets.QDoubleSpinBox, 'findpes_emin')
        self.findpes_emax = self.findChild(QtWidgets.QDoubleSpinBox, 'findpes_emax')
        self.findpes_state = self.findChild(QtWidgets.QSpinBox, 'findpes_state')
        self.findpes_tol = self.findChild(QtWidgets.QDoubleSpinBox, 'findpes_tol')
        # group box 'clean database options'
        self.clean_testint = self.findChild(QtWidgets.QCheckBox, 'clean_testint')
        self.clean_rmdup = self.findChild(QtWidgets.QCheckBox, 'clean_rmdup')
        self.clean_mindb = self.findChild(QtWidgets.QDoubleSpinBox, 'clean_mindb')
        self.clean_rmfail = self.findChild(QtWidgets.QCheckBox, 'clean_rmfail')
        self.clean_rminterp = self.findChild(QtWidgets.QCheckBox, 'clean_rminterp')
        # group box 'query'
        self.sql_allowwrite = self.findChild(QtWidgets.QCheckBox, 'sql_allowwrite')
        self.sql_query = self.findChild(QtWidgets.QPlainTextEdit, 'sql_query')

    def connectObjects(self):
        '''
        Connects UI elements so they do stuff when interacted with.
        '''
        super().connectObjects()
        # in pes/apes box, show certain options only when checked
        for radio in self.findpes_task:
            radio.clicked.connect(self.findpesOptionChanged)
        # in clean database box, show certain options only when checked
        self.clean_rmdup.stateChanged.connect(self.cleanOptionChanged)
        self.clean_rmfail.stateChanged.connect(self.cleanOptionChanged)
        # have the sql query box grow in size instead of adding a scroll bar
        self.sql_query.textChanged.connect(self.sqlChanged)

    @QtCore.pyqtSlot()
    def findpesOptionChanged(self):
        '''
        Allows the user to change task-specific options depending on whether
        the interval task or the match task is selected
        '''
        options = {0: self.findpes_int_box, 1: self.findpes_mat_box}
        for radio, box in options.items():
            if self.findpes_task[radio].isChecked():
                box.show()
            else:
                box.hide()

    @QtCore.pyqtSlot()
    def cleanOptionChanged(self):
        '''
        Allows the user to change the duplicate removal tolerance if the remove
        duplicate box is checked, and the remove interpolated points checkbox
        if the remove failed points box is checked.
        '''
        self.clean_mindb.setEnabled(self.clean_rmdup.isChecked())
        self.clean_rminterp.setEnabled(self.clean_rmfail.isChecked())
        # uncheck box when disabled
        if self.clean_rminterp.isEnabled() is False:
            self.clean_rminterp.setChecked(False)

    @QtCore.pyqtSlot()
    def sqlChanged(self):
        '''
        Sets the height of the SQL query text edit high enough to show all the
        query without a scroll bar. This is definitely a hack so please replace
        this if there is a better way to do it.
        '''
        # hand-picked arbitary constants that magically work
        adj_height = 8 + 15 * self.sql_query.document().size().height()
        self.sql_query.setMinimumHeight(int(adj_height))

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
                case 'analdd_1': # plot dd calculation rate in log
                    self.calcrate()
                case 'analdd_2': # plot wavepacket basis function trajectories
                    self.gwptraj()
                case 'analdd_3': # inspect PES/APES in database
                    self.findpes()
                case 'analdd_4': # check or clean database
                    self.checkdb()
                case 'analdd_5': # query database
                    self.querydb()
        except Exception as e:
            # switch to text tab to see if there are any other explanatory errors
            self.window().tab_widget.setCurrentIndex(0)
            QtWidgets.QMessageBox.critical(self.window(), 'Error', f'{type(e).__name__}: {e}')

    def calcrate(self):
        '''
        Reads the log and looks for lines of the following format

        time[fs]       t1
        ...
        No. QC calculations :     N1.1
        ...
        No. QC calculations :     N1.n
        ... (etc)

        and plots the number of calculations per timestep against time.
        '''
        filepath = self.window().cwd/'log'
        if filepath.is_file() is False:
            raise FileNotFoundError('Cannot find log file in directory')
        times = []
        n_calcs = []
        self.window().text.clear()
        with open(filepath, mode='r', encoding='utf-8') as f:
            for line in f:
                self.window().text.appendPlainText(line[:-1])
                # find a line with time[fs] in it and get time
                if re.search(r'time\[fs\]', line):
                    try:
                        time = float(re.search(r'[+-]?\d+(?:\.\d*)?', line)[0])
                        times.append(time)
                        n_calcs.append(0)
                    except:
                        pass
                # find a line with No. QC calculations in it and get n_calc
                if re.search(r'No\. QC calculations :', line):
                    try:
                        n_calc = int(re.search(r'\d+', line)[0])
                        n_calcs[-1] += n_calc
                    except:
                        pass
        if len(times) == 0:
            # nothing found?
            raise ValueError('Invalid log file')
        self.window().data = np.array([times, n_calcs])

        # start plotting, depending on options
        self.window().graph.reset(switch_to_plot=True)
        self.window().graph.setLabels(title='Calculations per time step',
                                      bottom='Time (fs)', left='QC calculations')
        self.window().graph.plot(self.window().data[0, :], self.window().data[1, :],
                                 name='QC calculations', pen='r')

    def gwptraj(self):
        '''
        Reads the file output of using gwptraj -trj, which is expected to be
        in the format, where each cell is a float,

        t.1    A1.1   A2.1   ...   An.1   B1.1   ...   Bn.1   ... repeat for momenta
        t.2    A1.2   A2.2   ...   An.2   B1.2   ...   Bn.2   ... repeat for momenta
        ...    ...    ...    ...   ...    ...    ...   ...    ... repeat for momenta
        t.m    A1.m   A2.m   ...   An.m   B1.m   ...   Bn.m   ... repeat for momenta

        where t is time, ABCDE... are gaussian wavepackets (GWPs), and 1...n
        are the modes. The columns are then repeated for momenta instead of
        GWP center coordinates.

        Plots the GWPs' center or momentum for a given mode. No legend is
        output.
        '''
        # -trj outputs a trajectory file only
        self.runCmd('gwptraj', '-trj')
        filepath = self.window().cwd/'trajectory'
        # assemble data matrix
        with open(filepath, mode='r', encoding='utf-8') as f:
            self.readFloats(f, None)

        # add contents of showd1d.log to text view
        filepath = self.window().cwd/'gwptraj.log'
        if filepath.is_file():
            with open(filepath, mode='r', encoding='utf-8') as f:
                self.window().text.appendPlainText(f'{"-"*80}\n{f.read()}')

        # find ngwp from input. if input not found ask user for value
        try:
            with open(self.window().cwd/'input', mode='r',
                      encoding='utf-8') as f:
                txt = f.read()
                # IndexError raised when ngwp not found
                ngwp = int(re.findall(r'ngwp\s*?=\s*?(\d+)', txt)[0])
        except (FileNotFoundError, IndexError):
            ngwp, ok = QtWidgets.QInputDialog.getInt(
                parent=self.window(),
                title='Input ngwp',
                label='Cannot find input file or read ngwp from input file.'
                'Please enter the number of GWPs present (this should be ngwp'
                'value in input)',
                minValue=1
            )
            if not ok:
                raise ValueError('User cancelled operation') from None

        mode = self.gwptraj_mode.value()
        # the number of columns is 2*number of gaussians*number of modes. the
        # 2 is from the momenta being written after the gwp centers
        ncol = self.window().data.shape[1]
        nmode = ncol//(2*ngwp)
        if mode > nmode:
            raise ValueError(f'Mode {mode} is larger than number of modes {nmode}')
        # start plotting
        self.window().graph.reset(switch_to_plot=True)
        if self.gwptraj_task.currentIndex() == 0:
            # task is plot centre coordinates, which make up the first half of
            # the columns in trajectory file
            offset = mode
            self.window().graph.setLabels(title='GWP function centre coordinates',
                                          bottom='Time (fs)', left='GWP Center (au)')
        else:
            # task is plot momentum, which make up the second half of the
            # columns in trajectory file
            offset = ncol//2 + mode
            self.window().graph.setLabels(title='GWP function momentum',
                                          bottom='Time (fs)', left='GWP Momentum (au)')
        # plot line for each gaussian. columns are written for each gaussian
        # with ascending mode. to pick the gaussians for one mode we skip
        # nmode columns each time until we get to ngwp lines
        for i, col in enumerate(range(offset, offset+ngwp*nmode, nmode)):
            self.window().graph.plot(self.window().data[:, 0], self.window().data[:, col],
                                     pen=(i, ngwp))

    def findpes(self):
        '''
        Find database entries in the pes/apes + geo table where energies are
        within a certain user-defined interval or where energies between two
        states match within a tolerance.
        '''
        filepath = self.window().cwd/'database.sql'
        if filepath.is_file() is False:
            raise FileNotFoundError('Cannot find database.sql file in directory')
        con = sqlite3.connect(f'file:{filepath}?mode=ro', uri=True,
                              timeout=float(self.window().timeout_spinbox.value()))
        cur = con.cursor()
        # the number of electronic states
        nroot = cur.execute('SELECT Nroot FROM refdb;').fetchone()[0]
        # the table to select entries
        table = {0: 'pes', 1: 'apes'}[self.findpes_type.currentIndex()]
        # generate the query. it will be a sequence of strings joined together
        # with UNION, as a query is generated for each electronic state.
        # nb: the method here uses f strings which is generally unsafe as it
        # is vulnerable to sql injection. however, the user has access to the
        # entire database anyway, so this is not an issue.
        query = []
        if self.findpes_task[0].isChecked():
            # task is find energies between interval
            emin = self.findpes_emin.value()
            emax = self.findpes_emax.value()
            description = (f'Finding database entries in {table} where '
                           f'energies between {emin} and {emax}')
            for s in range(1, nroot+1):
                if table == 'pes':
                    query.append(f'SELECT {s} AS "state", * FROM pes LEFT JOIN '
                                 f'geo USING(id) WHERE eng_{s}_{s} BETWEEN '
                                 f'{emin} AND {emax}')
                else:
                    query.append(f'SELECT {s} AS "state", * FROM apes LEFT JOIN '
                                 f'geo USING(id) WHERE eng_{s} BETWEEN {emin} '
                                 f'AND {emax}')
        else:
            # task is find matching energies
            s1 = self.findpes_state.value()
            tol = self.findpes_tol.value()
            if s1 > nroot:
                raise ValueError(f'State {s1} cannot be greater than number of'
                                 f'states {nroot}')
            description = (f'Finding database entries in {table} where '
                           f'energies match state {s1} (abs. tol. {tol})')
            for s2 in range(1, nroot+1):
                if s2 == s1:
                    continue
                elif table == 'pes':
                    query.append(f'SELECT {s1} AS "state1", {s2} AS "state2", * '
                                 f'FROM pes LEFT JOIN geo USING(id) WHERE '
                                 f'ABS(eng_{s2}_{s2} - eng_{s1}_{s1}) <= {tol}')
                else:
                    query.append(f'SELECT {s1} AS "state1", {s2} AS "state2", * '
                                 f'FROM apes LEFT JOIN geo USING(id) WHERE '
                                 f'ABS(eng_{s2} - eng_{s1}) <= {tol}')
        query = '\nUNION\n'.join(query) + ';'
        res = cur.execute(query).fetchall()
        con.close()

        # format result
        self.window().tab_widget.setCurrentIndex(0)
        if res:
            post=f'Query was:\n{query}'
        else:
            post=f'No rows returned\n\nQuery was:\n{query}'
        self.window().writeTable(res, header=[col[0] for col in cur.description],
                                 pre=description, post=post)

    def checkdb(self):
        '''
        Executes the checkdb command with options depending on which options
        the user has chosen.
        '''
        clean_options = []
        if self.clean_testint.isChecked():
            clean_options.append('-rd')
        if self.clean_rmdup.isChecked():
            clean_options.append('-d')
            clean_options.extend(['-mindb', str(self.clean_mindb.value())])
        if self.clean_rminterp.isChecked():
            clean_options.append('-sc')
        elif self.clean_rmfail.isChecked():
            clean_options.append('-c')
        # switch to text view to see output
        self.window().tab_widget.setCurrentIndex(0)
        self.runCmd('checkdb', *clean_options)

    def querydb(self):
        '''
        Executes a user-written SQL query on database.sql. Returns the result
        with nice formatting.
        '''
        query = self.sql_query.toPlainText()
        filepath = self.window().cwd/'database.sql'
        if filepath.is_file() is False:
            raise FileNotFoundError('Cannot find database.sql file in directory')
        if self.sql_allowwrite.isChecked():
            mode = 'rw'
        else:
            mode = 'ro'
        con = sqlite3.connect(f'file:{filepath}?mode={mode}', uri=True,
                              timeout=float(self.window().timeout_spinbox.value()),
                              isolation_level=None)
        cur = con.cursor()
        res = cur.execute(query).fetchall()
        con.close()

        # format result
        self.window().tab_widget.setCurrentIndex(0)
        if res:
            post=None
        else:
            post='No rows returned'
        self.window().writeTable(res, header=[col[0] for col in cur.description],
                                 pre=f'Executing:\n{query}\n', post=post)
