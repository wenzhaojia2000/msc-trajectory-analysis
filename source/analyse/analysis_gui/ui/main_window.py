# -*- coding: utf-8 -*-
'''
@author: 19081417

Consists of the single class that provides the functionality for the main
window, including menus and the directory edit.
'''

from pathlib import Path
import subprocess
from PyQt5 import QtWidgets, QtCore, QtGui, uic

from .core import AnalysisBase, AnalysisMeta
from .custom_plot import CustomPlotWidget
from .custom_text import CustomTextWidget
from ..analysis.convergence import AnalysisConvergence
from ..analysis.integrator import AnalysisIntegrator
from ..analysis.results import AnalysisResults
from ..analysis.system import AnalysisSystem
from ..analysis.direct_dynamics import AnalysisDirectDynamics

class AnalysisMain(AnalysisBase, QtWidgets.QMainWindow, metaclass=AnalysisMeta):
    '''
    UI of the main window.
    '''
    def __init__(self):
        '''
        The method that is called when the instance is initialised.
        '''
        # call the inherited class' __init__ method
        super().__init__()
        # load the .ui file (from the folder this .py file is in rather than
        # wherever this is executed)
        uic.loadUi(Path(__file__).parent/'quantics_analysis.ui', self)
        # activate analysis tabs. these classes dictate functionality for each
        # analysis tab
        for class_, object_name in zip(
                [AnalysisConvergence, AnalysisIntegrator, AnalysisResults,
                 AnalysisSystem, AnalysisDirectDynamics],
                ['analconv_tab', 'analint_tab', 'analres_tab',
                 'analsys_tab', 'analdd_tab']
            ):
            self.findChild(class_, object_name)._activate()
        # set a main window icon. try to find the PsiPhi file in doc/graphics
        # (from file location, go up 4 folders for the main quantics directory)
        icon = Path(__file__).parents[4]/'doc/graphics/PsiPhi_logo.png'
        self.setWindowIcon(QtGui.QIcon(str(icon)))

        self.findObjects()
        self.connectObjects()
        # set text in dir_edit to be the current working directory
        self.directoryChanged()
        # data (array or numpy array) that is used to display the plot, which
        # should be updated for each replot. may be accessed by signals in
        # animated plots. can be saved using the 'save .npy data' action in the
        # plot widget.
        self.data = None

    def findObjects(self):
        '''
        Finds objects from the loaded .ui file and set them as instance
        variables and sets some of their properties.
        '''
        # ui items
        self.dir_edit = self.findChild(QtWidgets.QLineEdit, 'dir_edit')
        self.dir_edit_dialog = self.findChild(QtWidgets.QToolButton, 'dir_edit_dialog')
        self.tab_widget = self.findChild(QtWidgets.QTabWidget, 'tab_widget')
        self.add_flags_box = self.findChild(QtWidgets.QGroupBox, 'add_flags_box')
        self.add_flags = self.findChild(QtWidgets.QLineEdit, 'add_flags')
        self.text = self.findChild(CustomTextWidget, 'output_text')
        self.graph = self.findChild(CustomPlotWidget, 'output_plot')
        # menu items
        self.timeout_menu = self.findChild(QtWidgets.QMenu, 'timeout_menu')
        self.menu_dir = self.findChild(QtWidgets.QAction, 'menu_dir')
        self.exit = self.findChild(QtWidgets.QAction, 'action_exit')
        self.cleanup = self.findChild(QtWidgets.QAction, 'cleanup')
        self.allow_add_flags = self.findChild(QtWidgets.QAction, 'allow_add_flags')
        self.no_command = self.findChild(QtWidgets.QAction, 'no_command')
        self.open_guide = self.findChild(QtWidgets.QAction, 'open_guide')
        # animated plot items
        self.media_box = self.findChild(QtWidgets.QWidget, 'output_media_box')
        self.scrubber = self.findChild(QtWidgets.QSlider, 'media_scrubber')
        self.ffstart = self.findChild(QtWidgets.QToolButton, 'media_ffstart')
        self.play = self.findChild(QtWidgets.QToolButton, 'media_play')
        self.ffend = self.findChild(QtWidgets.QToolButton, 'media_ffend')
        self.speed_button = self.findChild(QtWidgets.QPushButton, 'media_speed')
        self.speed = 30.0 # animation speed set by speed_button

        # set icons for tool buttons
        self.dir_edit_dialog.setIcon(self.getIcon('SP_DirLinkIcon'))
        self.ffstart.setIcon(self.getIcon('SP_MediaSkipBackward'))
        self.play.setIcon(self.getIcon('SP_MediaPlay'))
        self.ffend.setIcon(self.getIcon('SP_MediaSkipForward'))
        # hide additional flags box, scrubber and media buttons initially
        self.add_flags_box.hide()
        self.media_box.hide()

    def connectObjects(self):
        '''
        Connects objects so they do stuff when interacted with.
        '''
        # ui items
        self.dir_edit.editingFinished.connect(self.directoryChanged)
        self.dir_edit_dialog.clicked.connect(self.chooseDirectory)
        # menu items
        self.menu_dir.triggered.connect(self.chooseDirectory)
        self.exit.triggered.connect(lambda: self.close())
        self.cleanup.triggered.connect(self.cleanupDirectory)
        self.allow_add_flags.triggered.connect(self.showAddFlags)
        self.open_guide.triggered.connect(self.openUserGuide)
        # animated plot items
        self.ffstart.clicked.connect(lambda: self.scrubber.setValue(self.scrubber.minimum()))
        self.ffend.clicked.connect(lambda: self.scrubber.setValue(self.scrubber.maximum()))
        self.speed_button.clicked.connect(self.changeSpeed)
        # connect the play button to a timer
        self.play.clicked.connect(self.startStopAnimation)
        self.timer = QtCore.QTimer(self.play)
        self.timer.timeout.connect(
            lambda: self.scrubber.setValue(self.scrubber.value() + 1)
        )

        # add a timeout spinbox to the timeout menu
        self.timeout_spinbox = QtWidgets.QDoubleSpinBox(self)
        self.timeout_spinbox.setSuffix(' s')
        self.timeout_spinbox.setMaximum(86400)
        self.timeout_spinbox.setValue(60)
        self.timeout_spinbox.setDecimals(1)
        timeout_action = QtWidgets.QWidgetAction(self)
        timeout_action.setDefaultWidget(self.timeout_spinbox)
        self.timeout_menu.addAction(timeout_action)

    def getIcon(self, icon_name:str) -> QtGui.QIcon:
        '''
        Convenience function to get one of Qt's built in icons. See a list here:
            https://www.pythonguis.com/faq/built-in-qicons-pyqt/
        '''
        return self.style().standardIcon(getattr(QtWidgets.QStyle, icon_name))

    @property
    def cwd(self):
        '''
        Returns the Path object of the current directory.
        '''
        return Path(self.dir_edit.text())

    @QtCore.pyqtSlot()
    def directoryChanged(self):
        '''
        Action to perform when the user edits the directory textbox. The
        entered value must be a directory, otherwise raises an error.
        '''
        # set to cwd when the program is opened or everything is deleted
        if self.dir_edit.text() == '':
            self.dir_edit.setText(str(Path.cwd()))
        # if the path is invalid, change to last acceptable path and open
        # error popup
        elif Path(self.dir_edit.text()).is_dir() is False:
            self.dir_edit.undo()
            QtWidgets.QMessageBox.critical(self, 'Error',
                'NotADirectoryError: Directory does not exist or is invalid')
        # if path is valid, resolve it (change to absolute path without ./
        # or ../, etc)
        elif Path(self.dir_edit.text()).is_dir():
            self.dir_edit.setText(str(Path(self.dir_edit.text()).resolve()))

    @QtCore.pyqtSlot()
    def chooseDirectory(self):
        '''
        Allows user to choose a directory using a menu. Sets self.dir_edit
        (and thus self.cwd) when finished.
        '''
        dirname = QtWidgets.QFileDialog.getExistingDirectory(self,
            'Open directory', self.dir_edit.text(),
            options=QtWidgets.QFileDialog.Options()
        )
        if dirname:
            self.dir_edit.setText(dirname)

    @QtCore.pyqtSlot()
    def cleanupDirectory(self):
        '''
        Asks the user whether to delete any output files associated with
        analysis quantics programs (not from quantics itself), eg. trajectory
        from gwptraj, gpop.pl from rdgpop. If so, removes them.
        '''
        # glob-type filenames to remove
        # ^ means this file is not associated with a command that is called in
        # this ui
        file_glob = [
            'den1d_*',
            'dens2d_*', # ^dengen
            'spops',
            'trajectory',
            # pl files
            'gpop.pl',
            'natpop_*.pl',
            'qdq_*.pl',
            'spop.pl', # ^rdcheck spop (same function as statepop)
            'spectrum.pl',
            # log files
            'ausw.log',
            'dengen.log', # ^dengen
            'gwptraj.log',
            'norm.log',
            'ortho.log',
            'showd1d.log',
            'showsys.log',
            # xyz files
            'pes.xyz',
            'den2d.xyz',
        ]
        # find the output files actually present in the directory
        files = []
        for glob in file_glob:
            files.extend(list(self.cwd.glob(glob)))

        if files:
            clicked = QtWidgets.QMessageBox.question(
                self, 'Delete these files?', 'These files will be deleted:\n' +\
                '\n'.join([file.name for file in files])
            )
            if clicked == QtWidgets.QMessageBox.Yes:
                for file in files:
                    file.unlink()
                QtWidgets.QMessageBox.information(
                    self, 'Success', 'Deletion successful.'
                )
        else:
            QtWidgets.QMessageBox.information(
                self, 'No files found',
                'Found no analysis output files in this directory.'
            )

    @QtCore.pyqtSlot()
    def showAddFlags(self):
        '''
        Shows/hides the additional flags box if user allows additional flags
        in the menu.
        '''
        if self.allow_add_flags.isChecked():
            self.add_flags_box.show()
        else:
            self.add_flags_box.hide()

    @QtCore.pyqtSlot()
    def openUserGuide(self):
        '''
        Attempts to opens the User guide HTML file in the browser.
        '''
        url = Path(__file__).parents[4]/'doc/analyse/anal_gui/user_guide.html'
        # for windows os.startfile(url) should work but quantics doesn't run
        # on windows
        try:
            # mac and most native linux versions
            subprocess.run(['open', str(url)])
        except FileNotFoundError:
            try:
                # wsl: the best i can do is open windows explorer to the folder
                # where the file is.
                subprocess.run(['explorer.exe', '.'], cwd=url.parent)
            except FileNotFoundError:
                QtWidgets.QMessageBox.critical(
                    self, 'Couldn\'t open browser',
                    'Couldn\'t open the user guide. Try opening it yourself here\n' +\
                    str(url)
                )

    @QtCore.pyqtSlot()
    def startStopAnimation(self):
        '''
        Starts and stops the automatic playback of an animated plot.
        '''
        if self.play.isChecked():
            self.play.setIcon(self.style().standardIcon(
                QtWidgets.QStyle.SP_MediaPause
            ))
            self.timer.start(int(1000/self.speed))
        else:
            self.play.setIcon(self.style().standardIcon(
                QtWidgets.QStyle.SP_MediaPlay
            ))
            self.timer.stop()

    @QtCore.pyqtSlot()
    def changeSpeed(self):
        '''
        Opens a popup allowing the user to select a new playback speed.
        '''
        speed, ok = QtWidgets.QInputDialog.getDouble(
            self.window(),
            'Input speed',
            'Enter the animation playback speed or video framerate per second:',
            self.speed
        )
        if ok:
            self.speed = speed
