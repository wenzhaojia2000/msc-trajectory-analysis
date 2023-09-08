# -*- coding: utf-8 -*-
'''
@author: 19081417

Consists of the single class that provides the functionality for the text
widget.
'''

from math import isfinite
from PyQt5 import QtWidgets, QtCore

class CustomTextWidget(QtWidgets.QPlainTextEdit):
    '''
    Extends the capabilities of PyQt's QPlainTextEdit, allowing the user to
    change the line wrapping, allowing them to save the text to a file, and
    automatically formatting a table to text.

    This widget cannot function independently as it is tied to the
    AnalysisMain class, referred to using self.window().
    '''

    def __init__(self, *args, **kwargs):
        '''
        Constructor method.
        '''
        super().__init__(*args, **kwargs)
        # menu actions
        self.save_text = QtWidgets.QAction('Save text')
        self.save_text.triggered.connect(self.saveText)
        self.line_wrap = QtWidgets.QAction('Line Wrap')
        self.line_wrap.setCheckable(True)
        self.line_wrap.triggered.connect(self.changeLineWrap)
        # requires contextMenuPolicy to be CustomContextMenu (should be set
        # in Qt designer)
        self.customContextMenuRequested.connect(self.showTextMenu)

    @QtCore.pyqtSlot(QtCore.QPoint)
    def showTextMenu(self, point:QtCore.QPoint):
        '''
        Shows a custom context menu when right-clicking on the text view.
        '''
        # create a standard menu (with copy and select all) and add to it
        text_menu = self.createStandardContextMenu(point)
        # when right-clicked, add the extra actions in __init__ and show the
        # menu at the point (mapToGlobal to translate to where window is)
        text_menu.exec_(
            text_menu.actions() + [self.save_text, self.line_wrap],
            self.mapToGlobal(point)
        )

    @QtCore.pyqtSlot()
    def saveText(self):
        '''
        Saves an .txt file of the current text in the text view.
        '''
        # obtain a savename for the file
        savename, ok = QtWidgets.QFileDialog.getSaveFileName(self,
            "Save File", str(self.window().cwd / 'Untitled.txt'),
            "Text (*.txt);;All files (*)"
        )
        if not ok:
            # user cancels operation
            return None
        with open(savename, mode='w', encoding='utf-8') as s:
            s.write(self.toPlainText())
        QtWidgets.QMessageBox.information(
            self, 'Success', 'Save text successful.'
        )
        return None

    @QtCore.pyqtSlot()
    def changeLineWrap(self):
        '''
        Changes the line wrapping in the text view.
        '''
        if self.line_wrap.isChecked():
            self.setLineWrapMode(self.WidgetWidth)
        else:
            self.setLineWrapMode(self.NoWrap)

    def writeTable(self, table:list, header:list=None, colwidth:int=16,
                   pre:str=None, post:str=None):
        '''
        Function that writes a table (list of lists or tuples) into a formatted
        table written into self.

        Ensure strings and integers are less than the column width (floats are
        automatically formatted to be fixed width). The default width is 16
        with 1 space of padding.

        header is a list of column names which is shown above the table. pre
        and post are strings that are printed before and after the table,
        respectively.
        '''
        if colwidth < 8:
            raise ValueError('colwidth cannot be lower than 8')
        # obtain border length, the number of hyphens to section off
        if len(table) > 0:
            border_len = len(table[0]) * (colwidth + 1)
        elif header:
            border_len = len(header) * (colwidth + 1)
        else:
            border_len = 0

        self.clear()
        if pre:
            self.appendPlainText(pre)
        self.appendPlainText('-'*border_len)
        # print header, wrapped by hyphens
        if header:
            header = ''.join([f'{{:>{colwidth}}} '.format(col) for col in header])
            self.appendPlainText(header)
            self.appendPlainText('='*border_len)
        # print out results
        for row in table:
            out = ''
            for cell in row:
                if isinstance(cell, float) and isfinite(cell):
                    # scientific format with 9 dp (8 dp if |exponent| > 100)
                    if abs(cell) >= 1e+100 or 0 < abs(cell) <= 1e-100:
                        out += f'{{: .{colwidth-8}e}} '.format(cell)
                    else:
                        out += f'{{: .{colwidth-7}e}} '.format(cell)
                else:
                    # align right with width 16 (str() allows None to be formatted)
                    out += f'{{:>{colwidth}}} '.format(str(cell))
            self.appendPlainText(out)
        # show bottom border only if there is at least one result
        if len(table) > 0:
            self.appendPlainText('-'*border_len)
        if post:
            self.appendPlainText(post)
