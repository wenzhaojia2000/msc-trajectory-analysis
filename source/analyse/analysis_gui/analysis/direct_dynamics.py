# -*- coding: utf-8 -*-
'''
@author: 19081417

Consists of the single class that provides functionality for the 'Analyse
Direct Dynamics' tab of the analysis GUI.
'''

from pathlib import Path
import re
import sqlite3
import numpy as np
from PyQt5 import QtWidgets, QtCore
from pyqtgraph import intColor as colr
from ..ui.analysis_tab import AnalysisTab

class AnalysisDirectDynamics(AnalysisTab):
    '''
    Promoted widget that defines functionality for the 'Analyse Direct
    Dynamics' tab of the analysis GUI.
    '''
    def __init__(self):
        '''
        Constructor method. Loads the UI file.
        '''
        super().__init__(Path(__file__).parent/'direct_dynamics.ui')

    def activate(self):
        '''
        Activation method. See the documentation in AnalysisTab._activate for
        information.
        '''
        methods = {
            0: self.calcrate, # plot dd calculation rate in log
            1: self.gwptraj,  # plot wavepacket basis function trajectories
            2: self.ddpesgeo, # inspect PES/APES in database
            3: self.checkdb,  # check or clean database
            4: self.querydb   # query database
        }
        options = {
            1: self.gwptraj_box,
            2: self.ddpesgeo_box,
            3: self.clean_box,
            4: self.sql_box
        }
        required_files = {
            0: ['log'],
            1: ['psi'],
            2: ['database.sql'],
            3: ['database.sql'],
            4: ['database.sql']
        }
        super().activate(methods, options, required_files)

        self.ddpesgeo_task = [self.ddpesgeo_int, self.ddpesgeo_mat]
        # one of the boxes inside ddpesgeo should be hidden
        self.ddpesgeoOptionChanged()
        # in pes/apes box, show certain options only when checked
        for radio in self.ddpesgeo_task:
            radio.clicked.connect(self.ddpesgeoOptionChanged)
        # in clean database box, show certain options only when checked
        self.clean_rmdup.stateChanged.connect(self.cleanOptionChanged)
        self.clean_rmfail.stateChanged.connect(self.cleanOptionChanged)
        # have the sql query box grow in size instead of adding a scroll bar
        self.sql_query.textChanged.connect(self.sqlChanged)

    @QtCore.pyqtSlot()
    def ddpesgeoOptionChanged(self):
        '''
        Allows the user to change task-specific options depending on whether
        the interval task or the match task is selected
        '''
        options = {0: self.ddpesgeo_int_box, 1: self.ddpesgeo_mat_box}
        for radio, box in options.items():
            if self.ddpesgeo_task[radio].isChecked():
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
        filepath = self.window().dir.cwd/'log'
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
                    except ValueError:
                        pass
                # find a line with No. QC calculations in it and get n_calc
                if re.search(r'No\. QC calculations :', line):
                    try:
                        n_calc = int(re.search(r'\d+', line)[0])
                        n_calcs[-1] += n_calc
                    except ValueError:
                        pass
        if len(times) == 0:
            # nothing found?
            raise ValueError('Invalid log file')
        self.window().data = np.array([times, n_calcs])

        # start plotting, depending on options
        self.window().plot.reset(switch_to_plot=True)
        self.window().plot.setLabels(title='Calculations per time step',
                                      bottom='Time (fs)', left='QC calculations')
        self.window().plot.plot(self.window().data[0, :], self.window().data[1, :],
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
        filepath = self.window().dir.cwd/'trajectory'
        # assemble data matrix
        with open(filepath, mode='r', encoding='utf-8') as f:
            self.window().data = self.readFloats(f)

        # add contents of showd1d.log to text view
        filepath = self.window().dir.cwd/'gwptraj.log'
        if filepath.is_file():
            with open(filepath, mode='r', encoding='utf-8') as f:
                self.window().text.appendPlainText(f'{"-"*80}\n{f.read()}')

        # find ngwp from input. if input not found ask user for value
        try:
            with open(self.window().dir.cwd/'input', mode='r',
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
        self.window().plot.reset(switch_to_plot=True)
        if self.gwptraj_task.currentIndex() == 0:
            # task is plot centre coordinates, which make up the first half of
            # the columns in trajectory file
            offset = mode
            self.window().plot.setLabels(title='GWP function centre coordinates',
                                          bottom='Time (fs)', left='GWP Center (au)')
        else:
            # task is plot momentum, which make up the second half of the
            # columns in trajectory file
            offset = ncol//2 + mode
            self.window().plot.setLabels(title='GWP function momentum',
                                          bottom='Time (fs)', left='GWP Momentum (au)')
        # plot line for each gaussian. columns are written for each gaussian
        # with ascending mode. to pick the gaussians for one mode we skip
        # nmode columns each time until we get to ngwp lines
        for i, col in enumerate(range(offset, offset+ngwp*nmode, nmode)):
            self.window().plot.plot(self.window().data[:, 0], self.window().data[:, col],
                                     pen=colr(i, ngwp, maxValue=200))

    def ddpesgeo(self):
        '''
        Finds molecule geometries where energies of the PES/APES are within
        a certain user-defined interval or where energies between two states
        match within a tolerance.

        The output in text view is in the form

        STATE X [& Y] {

            ID: 12345
            ----------------------------------------
                     eng_X |           eng_Y |   ... (relevant states highlighted)
            1.23456789e+01 |  1.23456789e+01 |   ...
            ----------------------------------------
            Atom 1       x y z
            Atom 2       x y z
            ...

            ... repeat for all matches

        }
        ... repeat for more states
        '''
        filepath = self.window().dir.cwd/'database.sql'
        con = sqlite3.connect(f'file:{filepath}?mode=ro', uri=True,
                              timeout=self.window().timeout.value())
        cur = con.cursor()
        version = cur.execute('SELECT dbversion FROM versions;').fetchone()[0]
        match version:
            case 4:
                self._ddpesgeoV4(con, cur)
            case x:
                raise NotImplementedError('ddpesgeo not implemented for DB'
                                         f'version {x}')

    def _ddpesgeoV4(self, con:sqlite3.Connection, cur:sqlite3.Cursor):
        '''
        ddpesgeo implemented for DB version 4. See docstring for ddpesgeo for
        more details.
        '''
        # the number of electronic states
        nroot = cur.execute('SELECT Nroot FROM refdb;').fetchone()[0]
        # dictionary of the form {state(s) (frozenset): [list of entries]}
        # where an entry is also a dict of form {id (int), energy (tuple),
        # geo (np.ndarray where columns are x y z)}
        pesgeo = {}
        # since we join pes/apes table to geo but want to seperate the two
        # after sql query, need to find the number of columns in geo table (not
        # counting id so -1)
        geo_length = cur.execute(
            'SELECT COUNT(*) FROM pragma_table_info("geo");'
        ).fetchall()[0][0] - 1
        # get atom names in refdbrefgeom
        atom_names = [col[0] for col in cur.execute(
            'SELECT name FROM refdbrefgeom;'
        ).fetchall()]

        if self.ddpesgeo_type.currentIndex() == 0:
            table = 'pes'
            # dictionary mapping states to column names
            state_name = {s: f'eng_{s}_{s}' for s in range(1, nroot+1)}
        else:
            table = 'apes'
            state_name = {s: f'eng_{s}' for s in range(1, nroot+1)}

        if self.ddpesgeo_task[0].isChecked():
            # task is find energies between interval
            emin = self.ddpesgeo_emin.value()
            emax = self.ddpesgeo_emax.value()
            description = (f'Finding database entries in {table} where '
                           f'energies between {emin} and {emax}')
            # retrieve matching id + energies
            for s in range(1, nroot+1):
                query = (f'SELECT * FROM {table} LEFT JOIN geo USING(id) '
                         f'WHERE {state_name[s]} BETWEEN {emin} AND {emax};')
                res = cur.execute(query).fetchall()
                # add id, energies, geo. split geo into geo_length subarrays
                # so there are 3 columns
                pesgeo[frozenset({s})] = [{
                    'id': entry[0], 'energies': entry[1:-geo_length],
                    'geo': np.split(np.array(entry[-geo_length:]), geo_length//3)
                } for entry in res]
        else:
            # task is find matching energies
            s1 = self.ddpesgeo_state.value()
            tol = self.ddpesgeo_tol.value()
            description = (f'Finding database entries in {table} where '
                           f'energies match state {s1} (abs. tol. {tol})')
            if s1 > nroot:
                raise ValueError(f'State {s1} cannot be greater than number of '
                                 f'states {nroot}')
            for s2 in range(1, nroot+1):
                if s2 == s1:
                    continue
                else:
                    query = (f'SELECT * FROM {table} LEFT JOIN geo USING(id)'
                             f'WHERE ABS({state_name[s2]} - {state_name[s1]}) <= {tol};')
                res = cur.execute(query).fetchall()
                # add id, energies, geo. split geo into geo_length subarrays
                # so there are 3 columns
                pesgeo[frozenset({s1, s2})] = [{
                    'id': entry[0], 'energies': entry[1:-geo_length],
                    'geo': np.split(np.array(entry[-geo_length:]), geo_length//3)
                } for entry in res]

        # format result and set text
        self.window().text.clear()
        # column names in the pes/apes table, but don't include id
        col_names = [col[0] for col in cur.execute(
            f'SELECT name FROM pragma_table_info("{table}");'
        ).fetchall() if col[0] != 'id']
        # html to add to self.window().text
        html = f'<pre>{description}</pre><br/>'
        for states, entries in pesgeo.items():
            html += (f'<pre>STATE <b>{" & ".join(str(state) for state in states)}</b> '
                     '{</pre><br/>')
            for id_, energies, geo in [entry.values() for entry in entries]:
                header = []
                values = []
                # format col_names and energies into a table
                # if relevant state, make energy header and value bold
                for i, name in enumerate(col_names):
                    if name in [state_name[state] for state in states]:
                        header.append(f'<b>{name:>15}</b>')
                        values.append('<b>' + '{: .8e}'.format(energies[i]) + '</b>')
                    else:
                        header.append('{:>15}'.format(name))
                        values.append('{: .8e}'.format(energies[i]))
                html += (f'<pre>    ID: {id_}</pre>'
                         f'<pre>    {"-"*16*len(header)}</pre>'
                         f'<pre>    {" ".join(header)}</pre>'
                         f'<pre>    {" ".join(values)}</pre>'
                         f'<pre>    {"-"*16*len(header)}</pre>')
                # format the geometries
                for atom_name, xyz in zip(atom_names, geo):
                    # format array, remove brackets at start and end
                    xyz = np.array2string(xyz, formatter={
                        'float': lambda x: '{: .8e}'.format(x)
                    })[1:-1]
                    html += f'<pre>    {atom_name:>3} {xyz}</pre>'
                html += '<br/>'
            html += '<pre>}</pre><br/>'
        con.close()
        self.window().tab_widget.setCurrentIndex(0)
        self.window().text.appendHtml(html)

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
        filepath = self.window().dir.cwd/'database.sql'
        if self.sql_allowwrite.isChecked():
            mode = 'rw'
        else:
            mode = 'ro'
        con = sqlite3.connect(f'file:{filepath}?mode={mode}', uri=True,
                              timeout=float(self.window().timeout.value()),
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
        self.window().text.writeTable(res, header=[col[0] for col in cur.description],
                                      pre=f'Executing:\n{query}\n', post=post)
