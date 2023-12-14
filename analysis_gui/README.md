Quantics Analysis GUI package
-----------------------------

This package contains the code for the Quantics Analysis GUI. More information is available in the documentation in the `$ROOT_DIR/doc/` directory.

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
python3 $ROOT_DIR/quantics_analysis_gui.py
```

Alternatively, you can open the GUI from anywhere as long as `$ROOT_DIR` is on $PYTHONPATH (which you can modify using `sys.path`).

For developers
==============

Developers of the progam will also need Qt Designer to modify the .ui files in the directory. This is available as a standalone from a third party [here](https://build-system.fman.io/qt-designer-download), or from pip (`pyqt5-tools`).

Qt's official editor, Qt Creator, is not needed for this project!

To run tests, simply run the tests/run_tests.py file with python. This file automatically finds any test files starting with `test_` and runs them. You can also use

```
python3 $ROOT_DIR/quantics_analysis_gui.py -test
```