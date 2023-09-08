# -*- coding: utf-8 -*-
'''
@author: 19081417

Consists of the single class that provides the functionality for the media
widget, which controls the playback for animated plots.
'''

from pathlib import Path
from PyQt5 import QtWidgets, QtCore, uic

class MediaWidget(QtWidgets.QWidget):
    '''
    Provides a scrubber, which controls time in an animated plot, and several
    buttons for fast-forward to start, play/pause, fast-forward to end, and
    controlling playback speed.
    '''
    def __init__(self, *args, **kwargs):
        '''
        Constructor method. Setup to make the widget work, including connecting
        objects.
        '''
        super().__init__(*args, **kwargs)
        uic.loadUi(Path(__file__).parent/'media_widget.ui', self)

        # set icons for buttons
        for button, icon in [(self.ffstart, 'SP_MediaSkipBackward'),
                             (self.play, 'SP_MediaPlay'),
                             (self.ffend, 'SP_MediaSkipForward')]:
            button.setIcon(
                self.style().standardIcon(getattr(QtWidgets.QStyle, icon))
            )

        # connect objects
        self.ffstart.clicked.connect(lambda: self.scrubber.setValue(self.scrubber.minimum()))
        self.ffend.clicked.connect(lambda: self.scrubber.setValue(self.scrubber.maximum()))
        self.speed_button.clicked.connect(self.changeSpeed)
        # connect the play button to a timer
        self.play.clicked.connect(self.startStopAnimation)
        self.timer = QtCore.QTimer(self.play)
        self.timer.timeout.connect(
            lambda: self.scrubber.setValue(self.scrubber.value() + 1)
        )
        # playback speed that can be set by self.changeSpeed
        self.speed = 30.0

    @QtCore.pyqtSlot()
    def startStopAnimation(self):
        '''
        Starts and stops the automatic playback of an animated plot.
        '''
        if self.play.isChecked():
            self.play.setIcon(
                self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause)
            )
            # increment one frame every [1000/speed] ms
            self.timer.start(int(1000/self.speed))
        else:
            self.play.setIcon(
                self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay)
            )
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
