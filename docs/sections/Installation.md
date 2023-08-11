Requirements
------------

* GIMP 2.8 or 2.10
* Python 2.7 or later from the 2.7.x series


Windows
-------

1. Make sure you have GIMP installed with support for Python scripting.
2. Locate the folder containing GIMP plug-ins - open GIMP and go to `Edit → Preferences → Folders → Plug-Ins`.
3. Extract the `batcher` folder to one of the folders identified in the previous step.


Linux
-----

### If GIMP is installed via Flatpak or AppImage

The easier way to install any Python-based GIMP plug-in is to use a GIMP installation bundled in Flatpak (which can be downloaded from the [official GIMP page](https://www.gimp.org/downloads/)) or AppImage.

1. Locate the folder containing GIMP plug-ins - open GIMP and go to `Edit → Preferences → Folders → Plug-Ins`.
2. Extract the `batcher` folder to one of the folders identified in the previous step.


### If GIMP is installed via package manager

This is the less recommended way of installing plug-ins as of recently as certain distributions may have missing packages that are required for successful running of Python GIMP plug-ins (due to these distributions dropping packages dependent on Python 2).

1. Install Python 2.7.
   Usually by default, Linux distributions offer Python 3, which does not work with GIMP 2.8 or 2.10.
2. Install packages enabling the use of Python for GIMP plug-ins.
	 This varies across distributions.
	 For instance, on Arch Linux, you must install the `python2-gimp` package.
3. Locate the folder containing GIMP plug-ins - open GIMP and go to `Edit → Preferences → Folders → Plug-Ins`.
4. Extract the `batcher` folder to one of the folders identified in the previous step.

To check if GIMP recognizes your Python 2.7 installation, open GIMP and run `Filters → Python-Fu → Console`.
The console must display `Python 2.7` or later from the 2.7.x series.
If this is not the case, open `/usr/lib/gimp/2.0/interpreters/pygimp.interp` and change its contents to the following:

    python=[path to Python 2.7 executable]
    /usr/bin/python=[path to Python 2.7 executable]
    :Python:E::py::python:

`[path to Python 2.7 executable]` is usually `/usr/bin/python` or `/usr/bin/python2.7`.


macOS
-----

1. Make sure you have Python 2.7 installed.
2. Locate the folder containing GIMP plug-ins - open GIMP and go to `Edit → Preferences → Folders → Plug-Ins`.
3. Extract the `batcher` folder to one of the folders identified in the previous step.
