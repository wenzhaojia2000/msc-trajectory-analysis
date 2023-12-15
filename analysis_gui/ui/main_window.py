# -*- coding: utf-8 -*-
'''
@author: 19081417

Consists of the single class that provides the functionality for the main
window, including menus.
'''

from pathlib import Path
import subprocess
from PyQt5 import QtWidgets, QtCore, QtGui, uic

class AnalysisMain(QtWidgets.QMainWindow):
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
        uic.loadUi(Path(__file__).parent/'main_window.ui', self)

        # set a main window icon. try to find the PsiPhi file in doc/graphics
        # (from file location, go up 4 folders for the main quantics directory)
        icon = Path(__file__).parents[4]/'doc/graphics/PsiPhi_logo.png'
        self.setWindowIcon(QtGui.QIcon(str(icon)))

        # hide additional flags box, media widget initially
        self.add_flags_box.hide()
        self.media.hide()
        # data (array or numpy array) that is used to display the plot, which
        # should be updated for each replot. may be accessed by signals in
        # animated plots. can be saved using the 'save .npy data' action in the
        # plot widget.
        self.data = None

        # connect objects
        # menu items
        self.menu_dir.triggered.connect(self.dir.chooseDirectory)
        self.exit.triggered.connect(lambda: self.close())
        self.cleanup.triggered.connect(self.cleanupDirectory)
        self.allow_add_flags.triggered.connect(self.showAddFlags)
        self.open_guide.triggered.connect(self.openUserGuide)

        # add a timeout spinbox to the timeout menu
        self.timeout = QtWidgets.QDoubleSpinBox(self)
        self.timeout.setSuffix(' s')
        self.timeout.setMaximum(86400)
        self.timeout.setValue(60)
        self.timeout.setDecimals(1)
        timeout_action = QtWidgets.QWidgetAction(self)
        timeout_action.setDefaultWidget(self.timeout)
        self.menu_timeout.addAction(timeout_action)

        # activate the analysis widgets
        for widget in [self.analconv, self.analint, self.analres, self.analsys, self.analdd]:
            widget.activate()

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
            files.extend(list(self.dir.cwd.glob(glob)))

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
        url = Path(__file__).parents[2]/'doc/user_guide.html'
        # for windows os.startfile(url) should work but quantics doesn't run
        # on windows
        try:
            # mac and most native linux versions
            subprocess.run(['open', str(url)], check=True)
        except FileNotFoundError:
            try:
                # wsl: the best i can do is open windows explorer to the folder
                # where the file is.
                subprocess.run(['explorer.exe', '.'], cwd=url.parent, check=False)
            except FileNotFoundError:
                QtWidgets.QMessageBox.critical(
                    self, 'Couldn\'t open browser',
                    'Couldn\'t open the user guide. Try opening it yourself here\n' +\
                    str(url)
                )
