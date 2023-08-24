# -*- coding: utf-8 -*-
"""
@author: 19081417

Consists of the single class that provides the functionality for the coordinate
selector widget.
"""

import re
from PyQt5 import QtWidgets, QtCore

class CoordinateSelector(QtWidgets.QWidget):
    '''
    A custom widget that allows the user to select a 'cut' along the DOFs, by
    listing each mode label in a subwidget and allowing the user to select 'x',
    'y', or a value in the spin box for each DOF.

    By using str(), returns the selection of the coordinate value for each DOF,
    one on each single line.

    Limitations:
        - Not yet possible to select a cut using a vector (or file)
        - Not yet possible to select coordinate bounds (xmin, xmax, ymin, ymax)
        - Not yet possible to select x, y, z units
        - Not yet possible to retrieve mode labels from a ML-BASIS-SECTION.
    '''

    def __init__(self, *args, **kwargs):
        '''
        Constructor method.

        For the widget to work, requires the following to be present in
        self.window():
            - QLineEdit self.window().dir_edit (and self.window().cwd)
        '''
        super().__init__(*args, **kwargs)
        # set a vertical box layout for this widget
        self.setLayout(QtWidgets.QVBoxLayout())
        self.mode_labels = None
        self.addModeLabels()

    def __str__(self) -> str:
        '''
        For each DOF, returns the mode label, then either 'x', 'y', or the
        value chosen by the user. If no 'x' value is chosen, raises an error.
        Returns an empty string if the widget contains no modes.

        Invoke using str(<this widget>).
        '''
        x_selected = False
        out = ''
        for i in range(self.layout().count()):
            label = self.layout().itemAt(i).widget().findChild(QtWidgets.QLabel)
            select = self.layout().itemAt(i).widget().findChild(QtWidgets.QComboBox)
            value = self.layout().itemAt(i).widget().findChild(QtWidgets.QDoubleSpinBox)
            if select is None:
                # this means the widget only contains a label saying
                # input/modes not found -> return empty string
                return ''
            if select.currentIndex() == 2:
                out += f'{label.text()} {value.value()}\n'
            else:
                if select.currentIndex() == 0:
                    x_selected = True
                out += f'{label.text()} {select.currentText()}\n'
        if not x_selected:
            raise ValueError('An x coordinate was not selected')
        return out

    @property
    def xcoord(self) -> str:
        '''
        Returns the mode label of the x coordinate chosen by the user. If
        no DOF is chosen to be 'x', returns None.
        '''
        for i in range(self.layout().count()):
            label = self.layout().itemAt(i).widget().findChild(QtWidgets.QLabel)
            select = self.layout().itemAt(i).widget().findChild(QtWidgets.QComboBox)
            if select.currentIndex() == 0:
                return label.text()

    @property
    def ycoord(self) -> str:
        '''
        Returns the mode label of the y coordinate chosen by the user. If
        no DOF is chosen to be 'y', returns None.
        '''
        for i in range(self.layout().count()):
            label = self.layout().itemAt(i).widget().findChild(QtWidgets.QLabel)
            select = self.layout().itemAt(i).widget().findChild(QtWidgets.QComboBox)
            if select.currentIndex() == 1:
                return label.text()

    def refresh(self):
        '''
        If the mode labels have changed (ie. directory was changed), clear all
        existing mode widgets and replace them with new ones.
        '''
        try:
            modes = self.findModeLabels()
            # only refresh if mode labels have changed
            if self.mode_labels != modes:
                self.clearWidget()
                self.mode_labels = modes
                self.addModeLabels()
        except FileNotFoundError:
            self.clearWidget()
            self.layout().addWidget(
                QtWidgets.QLabel('Input file not found. Press continue to\n'
                                 'manually insert coordinates.')
            )
        # set the height to be the combined widgets plus padding. there is
        # probably a better way to do this but neither self.adjustSize() or
        # self.updateGeometry() work.
        self.setFixedHeight(30 + 30*self.layout().count())

    def clearWidget(self):
        '''
        Removes all mode subwidgets from this widget.
        '''
        self.mode_labels = None
        while self.layout().count():
            child = self.layout().takeAt(0)
            if child.widget():
              child.widget().deleteLater()

    def findModeLabels(self) -> list:
        '''
        Returns the list of mode labels from the input file in the window's
        current directory. This list will be empty if the function cannot find
        any mode labels.
        '''
        with open(self.window().cwd/'input', mode='r', encoding='utf-8') as f:
            txt = f.read()
            # find modes in SPF-BASIS-SECTION
            spf_section = re.findall(r'SPF-BASIS-SECTION\n(.*)\nend-spf-basis-section',
                                     txt, re.DOTALL|re.IGNORECASE)
            # if section does not exist, might be direct dynamics. find in
            # nmode subsection in INITIAL-GEOMETRY-SECTION
            ddmode_section = re.findall(r'nmode\n(.*)\nend-nmode',
                                        txt, re.DOTALL|re.IGNORECASE)
            if spf_section:
                # a list of dofs are displayed before an = sign, with a list
                # of digits after (maybe including id keyword). these may be on
                # a single line. match the part before =, split by comma, then
                # remove surrounding whitespace.
                regex = r'(.+?)=(?:[ \d,]|id)*'
                modes = [mode.strip() for line in re.findall(regex, spf_section[0])\
                                      for mode in line.split(',')\
                                      if mode.strip() not in ['packets', 'gwp_type']]
            elif ddmode_section:
                # a list of dofs are the first entry in each line (assuming
                # mode names can't have whitespace in them).
                modes = re.findall(r'^\s*\S+', ddmode_section[0], re.MULTILINE)
            else:
                modes = []
        return modes

    def addModeLabels(self):
        '''
        Adds a mode subwidget for each mode label in self.mode_labels. The
        user can then change the coordinate (x, y, or value) for that DOF
        in the subwidget.

        If there is only one DOF, it must be the 'x' coordinate.
        '''
        if self.mode_labels:
            for i, mode in enumerate(self.mode_labels):
                # add a new widget for each dof
                mode_widget = QtWidgets.QWidget(self)
                mode_layout = QtWidgets.QHBoxLayout(mode_widget)
                mode_layout.setContentsMargins(QtCore.QMargins(0,0,0,0))
                mode_widget.setLayout(mode_layout)
                # add components to widget: a label, (x, y, value) selector
                # and a spinbox to choose the value if value is selected
                label = QtWidgets.QLabel(mode)
                select = QtWidgets.QComboBox()
                if len(self.mode_labels) == 1:
                    # only one dof: must be x
                    select.addItems(['x'])
                else:
                    select.addItems(['x', 'y', 'value'])
                    # set index of first two items to x, y, rest value.
                    select.setCurrentIndex(min(i, 2))
                select.currentIndexChanged.connect(self.selectChanged)
                value = QtWidgets.QDoubleSpinBox()
                value.setRange(float('-inf'), float('inf'))
                value.setDecimals(3)
                # if x or y disable the value box
                value.setEnabled(i >= 2)
                for widget in [label, select, value]:
                    mode_layout.addWidget(widget)
                self.layout().addWidget(mode_widget)
        else:
            self.layout().addWidget(
                QtWidgets.QLabel('Can\'t find modes in input file. Press\n'
                                 'continue to manually insert coordinates.')
            )

    @QtCore.pyqtSlot()
    def selectChanged(self):
        '''
        Allows the user to change the selection for each DOF depending on the
        following constraints:
            - If the coordinate is changed to 'value', allow the user to modify
              the value spinbox, otherwise disable it.
            - There can only be one 'x' coordinate and one 'y' coordinate at
              a single time.
        '''
        mode_changed = self.layout().indexOf(self.sender().parent())
        index_changed = self.sender().currentIndex()
        # disable value if changed to x or y
        value = self.sender().parent().findChild(QtWidgets.QDoubleSpinBox)
        value.setEnabled(index_changed >= 2)
        # if set to x or y, set any other x or y to value in other subwidgets
        # (as there can only be one mode which is set to x or y)
        if index_changed in [0, 1]:
            for i in range(self.layout().count()):
                if i == mode_changed:
                    continue
                select = self.layout().itemAt(i).widget().findChild(QtWidgets.QComboBox)
                value = self.layout().itemAt(i).widget().findChild(QtWidgets.QDoubleSpinBox)
                if select.currentIndex() == index_changed:
                    select.setCurrentIndex(2)
                    value.setEnabled(True)
