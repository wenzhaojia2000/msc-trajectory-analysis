Quantics Analysis GUI package
-----------------------------

This package contains the code for the Quantics Analysis GUI.

Installing prerequisites
========================

The packages used by the GUI are:

+ Python >= 3.10
+ PyQt5
+ pyqtgraph

For conda users, you can use the environment.yml file in the folder to download these prerequisites using

```
conda env create -f environment.yml
```

If the environment is already created, you can use

```
conda activate quantics_gui
```

For non-conda users, you can use pip to install the packages instead.

Opening the GUI
===============

The current folder serves as a *python package*, and thus the GUI cannot be run from this folder. In the folder above, there is a file named `quantics_analysis_gui.py` which opens the GUI from outside of the package:

```
python3 %QUANTICS_DIR%/source/analyse/quantics_analysis_gui.py
```

Alternatively, you can open the GUI from anywhere as long as `%QUANTICS_DIR%/source/analyse` is on $PYTHONPATH (which you can modify using `sys.path`).

For developers
==============

Developers of the progam will also need Qt Designer to modify the `./ui/quantics_analysis.ui` file. This is available as a standalone from a third party [here](https://build-system.fman.io/qt-designer-download), or from pip (`pyqt5-tools`)

Qt Designer also comes with Qt's official editor, Qt Creator. This is not needed for this project!