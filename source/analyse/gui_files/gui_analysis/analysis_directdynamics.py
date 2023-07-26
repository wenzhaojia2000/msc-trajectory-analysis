# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

from pathlib import Path
import re
import sqlite3
import numpy as np
from PyQt5 import QtWidgets, QtCore
from .ui_base import AnalysisMainInterface, AnalysisTab

class AnalysisDirectDynamics(AnalysisTab):
    '''
    Defines functionality for the "Analyse Direct Dynamics" tab of the analysis
    GUI.
    '''
    def __init__(self, parent:AnalysisMainInterface) -> None:
        '''
        Initiation method.
        '''
        super().__init__(parent=parent, push_name='analdd_push',
                         box_name='analdd_layout')

    def findObjects(self, push_name, box_name) -> None:
        '''
        Obtains UI elements as instance variables, and possibly some of their
        properties.
        '''
        super().findObjects(push_name, box_name)
        # group box 'pes/apes options'
        self.findpes_box = self.parent().findChild(QtWidgets.QGroupBox, 'findpes_box')
        self.findpes_task = [
            self.parent().findChild(QtWidgets.QRadioButton, 'findpes_int'),
            self.parent().findChild(QtWidgets.QRadioButton, 'findpes_mat')
        ]
        self.findpes_int_box = self.parent().findChild(QtWidgets.QFrame, 'findpes_int_box')
        self.findpes_mat_box = self.parent().findChild(QtWidgets.QFrame, 'findpes_mat_box')
        # group box 'clean database options'
        self.clean_box = self.parent().findChild(QtWidgets.QGroupBox, 'clean_box')
        self.clean_testint = self.parent().findChild(QtWidgets.QCheckBox, 'clean_testint')
        self.clean_rmdup = self.parent().findChild(QtWidgets.QCheckBox, 'clean_rmdup')
        self.clean_mindb = self.parent().findChild(QtWidgets.QDoubleSpinBox, 'clean_mindb')
        self.clean_rmfail = self.parent().findChild(QtWidgets.QCheckBox, 'clean_rmfail')
        self.clean_rminterp = self.parent().findChild(QtWidgets.QCheckBox, 'clean_rminterp')
        # group box 'query'
        self.sql_box = self.parent().findChild(QtWidgets.QGroupBox, 'sql_box')
        self.sql_allowwrite = self.parent().findChild(QtWidgets.QCheckBox, 'sql_allowwrite')
        self.sql_query = self.parent().findChild(QtWidgets.QPlainTextEdit, 'sql_query')
        # boxes are hidden initially
        self.findpes_box.hide()
        self.findpes_mat_box.hide()
        self.clean_box.hide()
        self.sql_box.hide()

    def connectObjects(self) -> None:
        '''
        Connects UI elements so they do stuff when interacted with.
        '''
        super().connectObjects()
        # show the update options box when certain result is selected
        for radio in self.radio:
            radio.clicked.connect(self.optionSelected)
        # in pes/apes box, show certain options only when checked
        for radio in self.findpes_task:
            radio.clicked.connect(self.findpesOptionChanged)
        # in clean database box, show certain options only when checked
        self.clean_rmdup.stateChanged.connect(self.cleanOptionChanged)
        self.clean_rmfail.stateChanged.connect(self.cleanOptionChanged)
        # have the sql query box grow in size instead of adding a scroll bar
        self.sql_query.textChanged.connect(self.sqlChanged)

    @QtCore.pyqtSlot()
    def optionSelected(self) -> None:
        '''
        Shows per-analysis options if a valid option is checked.
        '''
        options = {2: self.findpes_box, 3: self.clean_box, 4: self.sql_box}
        for radio, box in options.items():
            if self.radio[radio].isChecked():
                box.show()
            else:
                box.hide()

    @QtCore.pyqtSlot()
    def findpesOptionChanged(self) -> None:
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
    def cleanOptionChanged(self) -> None:
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
    def continuePushed(self) -> None:
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
                    # self.gwptraj()
                    raise NotImplementedError('Not implemented yet')
                case 'analdd_3': # inspect PES/APES in database
                    raise NotImplementedError('Not implemented yet')
                case 'analdd_4': # check or clean database
                    self.checkdb()
                case 'analdd_5': # query database
                    self.querydb()
        except Exception as e:
            # switch to text tab to see if there are any other explanatory errors
            self.parent().tab_widget.setCurrentIndex(0)
            QtWidgets.QMessageBox.critical(self.parent(), 'Error', f'{type(e).__name__}: {e}')

    def calcrate(self) -> None:
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
        filepath = Path(self.parent().dir_edit.text())/'log'
        if filepath.is_file() is False:
            raise FileNotFoundError('Cannot find log file in directory')
        times = []
        n_calcs = []
        self.parent().text.clear()
        with open(filepath, mode='r', encoding='utf-8') as f:
            for line in f:
                self.parent().text.appendPlainText(line[:-1])
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
        self.parent().data = np.array([times, n_calcs])

        # start plotting, depending on options
        self.parent().resetPlot(True)
        self.parent().setPlotLabels(title='Calculations per time step',
                                    bottom='Time (fs)', left='QC calculations')
        self.parent().graph.plot(self.parent().data[0, :], self.parent().data[1, :],
                                 name='QC calculations', pen='r')

    # def gwptraj(self) -> None:
    #     '''
    #     The trajectory file that this function reads has way more than is
    #     displayed when using the interactive cmd function (in eth_sql_5/
    #     there are 900 columns while only 30 are displayed at one time in the
    #     command line gnuplot).
    #     '''
    #     self.runCmd('gwptraj', '-trj')
    #     filepath = Path(self.parent().dir_edit.text())/'trajectory'
    #     # assemble data matrix
    #     with open(filepath, mode='r', encoding='utf-8') as f:
    #         self.readFloats(f, None)
    #     if self.parent().keep_files.isChecked() is False:
    #         # delete intermediate file
    #         filepath.unlink()

    #     # add contents of showd1d.log to text view
    #     filepath = Path(self.parent().dir_edit.text())/'gwptraj.log'
    #     if filepath.is_file():
    #         with open(filepath, mode='r', encoding='utf-8') as f:
    #             self.parent().text.appendPlainText(f'{"-"*80}\n{f.read()}')
    #         if self.parent().keep_files.isChecked() is False:
    #             filepath.unlink()

    #     # start plotting
    #     colours = ['r','g','b','c','m','y','k']
    #     self.parent().resetPlot(True)
    #     self.parent().setPlotLabels(title='GWP function centre coordinates',
    #                                 bottom='Time (fs)', left='Trajectory (au)')
    #     # plot line for each column
    #     for col in range(self.parent().data.shape[1]):
    #         self.parent().graph.plot(self.parent().data[:, 0], self.parent().data[:, col],
    #                                  name=col, pen=colours[col%7])

    def checkdb(self) -> None:
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
        self.parent().tab_widget.setCurrentIndex(0)
        self.runCmd('checkdb', *clean_options)

    def querydb(self) -> None:
        '''
        Executes a user-written SQL query on database.sql. Returns the result
        with nice formatting.
        '''
        query = self.sql_query.toPlainText()
        filepath = Path(self.parent().dir_edit.text())/'database.sql'
        if self.sql_allowwrite.isChecked():
            mode = 'rw'
        else:
            mode = 'ro'
        con = sqlite3.connect(f'file:{filepath}?mode={mode}', uri=True,
                              timeout=float(self.parent().timeout_spinbox.value()))
        cur = con.cursor()
        res = cur.execute(query).fetchall()
        con.close()

        # format result
        self.parent().tab_widget.setCurrentIndex(0)
        if res:
            post='No rows returned'
        else:
            post=None
        self.writeTable(res, header=[col[0] for col in cur.description],
                        pre=f'Executing:\n{query}\n', post=post)
