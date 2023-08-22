# -*- coding: utf-8 -*-
'''
@author: 19081417

Consists of the single class that provides functionality for the 'Analyse
Results' tab of the analysis GUI. A class instance of this should be included
in the main UI class.
'''

from PyQt5 import QtWidgets, QtCore
from .ui_base import AnalysisTab

class AnalysisResults(AnalysisTab):
    '''
    Promoted widget that defines functionality for the "Analyse Results" tab of
    the analysis GUI.
    '''
    def _activate(self):
        '''
        Activation method. See the documentation in AnalysisTab for more
        information.
        '''
        options = {
            1: 'autocol_box'
        }
        required_files = {
            0: ['auto'], 1: ['auto'], 2: ['eigval']
        }
        super()._activate(
            push_name='analres_push', radio_box_name='analres_radio',
            options=options, required_files=required_files
        )

    def findObjects(self, push_name:str, box_name:str):
        '''
        Obtains UI elements as instance variables, and possibly some of their
        properties.
        '''
        super().findObjects(push_name, box_name)
        # group box 'autocorrelation options'
        self.autocol_prefac = self.findChild(QtWidgets.QComboBox, 'autocol_prefac')
        self.autocol_emin = self.findChild(QtWidgets.QDoubleSpinBox, 'autocol_emin')
        self.autocol_emax = self.findChild(QtWidgets.QDoubleSpinBox, 'autocol_emax')
        self.autocol_unit = self.findChild(QtWidgets.QComboBox, 'autocol_unit')
        self.autocol_tau = self.findChild(QtWidgets.QDoubleSpinBox, 'autocol_tau')
        self.autocol_iexp = self.findChild(QtWidgets.QSpinBox, 'autocol_iexp')
        self.autocol_func = self.findChild(QtWidgets.QComboBox, 'autocol_filfunc')

    def connectObjects(self):
        '''
        Connects UI elements so they do stuff when interacted with.
        '''
        super().connectObjects()
        # in autocorrelation box, allow damping order to change if tau nonzero
        self.autocol_tau.valueChanged.connect(self.autocolOptionChanged)

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
                case 'analres_1': # plot autocorrelation function
                    self.rdauto()
                case 'analres_2': # plot spectrum from autocorrelation function
                    self.autospec()
                case 'analres_3': # plot eigenvalues from matrix diagonalisation
                    self.runCmd('rdeigval')
        except Exception as e:
            # switch to text tab to see if there are any other explanatory errors
            self.window().tab_widget.setCurrentIndex(0)
            QtWidgets.QMessageBox.critical(self.window(), 'Error', f'{type(e).__name__}: {e}')

    @QtCore.pyqtSlot()
    def autocolOptionChanged(self):
        '''
        Allows the user to change the damping order if the damping time is set
        to non-zero (ie. damping is enabled)
        '''
        self.autocol_iexp.setEnabled(bool(self.autocol_tau.value()))

    def rdauto(self):
        '''
        Reads the auto file, which is expected to be in the format, where each
        cell is a float,

        t.1    y1.1    y2.1    y3.1
        t.2    y1.2    y2.2    y3.2
        ...    ...     ...     ...
        t.m    y1.m    y2.m    y3.m

        where x is time, and y1, y2, y3 are the real, imaginary, and absolute
        value of the autocorrelation function. Headers are ignored.

        Plots the autocorrelation function. Note that this function does not
        use the 'rdauto' command, as it essentially just prints out the auto
        file anyway.
        '''
        filepath = self.window().cwd/'auto'
        # assemble data matrix
        with open(filepath, mode='r', encoding='utf-8') as f:
            self.window().text.setPlainText(f.read())
            f.seek(0)
            try:
                self.window().data = self.readFloats(f, 4)
            except ValueError:
                raise ValueError('Invalid auto file') from None

        # start plotting
        self.window().graph.reset(switch_to_plot=True)
        self.window().graph.setLabels(title='Autocorrelation function',
                                      bottom='Time (fs)', left='C(t)')
        self.window().graph.plot(self.window().data[:, 0], self.window().data[:, 1],
                                 name='Real autocorrelation', pen='r')
        self.window().graph.plot(self.window().data[:, 0], self.window().data[:, 2],
                                 name='Imag. autocorrelation', pen='b')
        self.window().graph.plot(self.window().data[:, 0], self.window().data[:, 3],
                                 name='Abs. autocorrelation', pen='g')

    def autospec(self):
        '''
        Reads the file output of using autospec, which is expected to be in
        the format, where each cell is a float,

        E.1    g0.1    g1.1    g2.1
        E.2    g0.2    g1.2    g2.2
        ...    ...     ...     ...
        E.m    g0.m    g1.m    g2.m

        where E is energy, and gn are the spectra of the various filter
        functions. Lines starting with '#' are ignored.

        Plots the spectrum of the autocorrelation function.
        '''
        # map of autocol_unit indices to command line argument (labels are different)
        autocol_unit_map = {0: 'ev', 1: 'au', 2: 'nmwl', 3: 'cm-1', 4: 'kcal/mol',
                            5: 'kj/mol', 6: 'invev', 7: 'kelvin', 8: 'debye',
                            9: 'mev', 10: 'mh', 11: 'aj'}
        # additional arguments for autocorrelation options
        autocol_options = [
            str(self.autocol_emin.value()),
            str(self.autocol_emax.value()),
            autocol_unit_map[self.autocol_unit.currentIndex()],
            str(self.autocol_tau.value()),
            str(self.autocol_iexp.value())
        ]
        # need -lin flag if user selects g3, g4 or g5
        if self.autocol_func.currentIndex() > 2:
            autocol_options.insert(0, '-lin')
        # choose prefactor
        match self.autocol_prefac.currentIndex():
            case 0:
                self.runCmd('autospec', '-FT', *autocol_options)
            case 1:
                self.runCmd('autospec', '-EP', *autocol_options)

        filepath = self.window().cwd/'spectrum.pl'
        # assemble data matrix
        with open(filepath, mode='r', encoding='utf-8') as f:
            self.window().data = self.readFloats(f, 4, ignore_regex=r'^#')

        # start plotting
        self.window().graph.reset(switch_to_plot=True)
        self.window().graph.setLabels(title='Autocorrelation spectrum',
                                      bottom=f'Energy ({self.autocol_unit.currentText()})',
                                      left='Spectrum')
        self.window().graph.plot(self.window().data[:, 0],
                                 self.window().data[:, self.autocol_func.currentIndex()%3+1],
                                 name='Autocorrelation spectrum', pen='r')
