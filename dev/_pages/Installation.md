---
title: Installation
permalink: /docs/installation/
---

## Requirements

Batcher requires [GIMP 3.0.0](https://www.gimp.org/downloads/) or later.

**On Windows, if you downloaded GIMP 3 before March 19, 2025, you will need to update GIMP (or download and install GIMP again if GIMP does not offer an update). There was originally an issue that prevented several plug-ins, including Batcher, from working.**


## Download

Batcher can currently be installed only manually by copying files from a ZIP archive.

**[Download latest release](https://github.com/kamilburda/batcher/releases/tag/1.1.1) (1.1.1, June 15, 2025)**


## Windows

1. **If you downloaded GIMP 3 before March 19, 2025, you will need to update GIMP (or download and install GIMP again if GIMP does not offer an update).** There was originally an issue that prevented several plug-ins, including Batcher, from working.
2. If you installed GIMP from gimp.org, make sure you enabled support for Python plug-ins (this is checked by default). The Microsoft Store version of GIMP enables Python support automatically.
3. Locate the folder containing GIMP plug-ins - open GIMP and go to `Edit → Preferences → Folders → Plug-Ins`. If you cannot locate any of the folders on your system, you can add a custom folder. 
4. Copy the `batcher` folder from the downloaded archive to one of the folders chosen in the previous step. The folder hierarchy should look like this:
    ```
    plug-ins/
        ...other plug-in folders...
        batcher/
            ...other Batcher files and folders...
            batcher.py
    ```
5. If you have GIMP opened, you must restart GIMP.


## Linux

### Flatpak

1. Copy the `batcher` folder from the downloaded archive to `/home/<your username>/.config/GIMP/<GIMP version>/plug-ins`, e.g. `/home/username/.config/GIMP/3.0/plug-ins` for GIMP 3.0.x versions. Create the folder if it does not exist. The folder hierarchy should look like this:
    ```
    plug-ins/
        ...other plug-in folders...
        batcher/
            ...other Batcher files and folders...
            batcher.py
    ```
2. If you have GIMP opened, you must restart GIMP.


### AppImage

1. Locate the folder containing GIMP plug-ins - open GIMP and go to `Edit → Preferences → Folders → Plug-Ins`. If you cannot locate any of the folders on your system, you can add a custom folder.
2. Copy the `batcher` folder from the downloaded archive to one of the folders chosen in the previous step. The folder hierarchy should look like this:
    ```
    plug-ins/
        ...other plug-in folders...
        batcher/
            ...other Batcher files and folders...
            batcher.py
    ```
3. If you have GIMP opened, you must restart GIMP.


### Snap

Currently not supported. 🥲 Any [help providing a Snap package](https://github.com/kamilburda/batcher/issues/123) is appreciated.


### Other installers or unofficial sources

1. If you installed GIMP and/or Batcher via a package manager, make sure the following dependencies are installed:
   * Python 3.7 or later
   * [Pycairo](https://pycairo.readthedocs.io/en/latest/) library, i.e. Python bindings for the cairo library, including GObject bindings. For example, on Debian-based distributions, `python3-gi-cairo` is required.
2. Locate the folder containing GIMP plug-ins - open GIMP and go to `Edit → Preferences → Folders → Plug-Ins`. If you cannot locate any of the folders on your system, you can add a custom folder.
3. Copy the `batcher` folder from the downloaded archive to one of the folders chosen in the previous step. The folder hierarchy should look like this:
    ```
    plug-ins/
        ...other plug-in folders...
        batcher/
            ...other Batcher files and folders...
            batcher.py
    ```
4. If you have GIMP opened, you must restart GIMP.


## macOS

1. Locate the folder containing GIMP plug-ins - open GIMP and go to `GIMP → Preferences (or Settings) → Folders → Plug-Ins`. If you cannot locate any of the folders on your system, you can add a custom folder. 
2. Copy the `batcher` folder from the downloaded archive to one of the folders chosen in the previous step. The folder hierarchy should look like this:
    ```
    plug-ins/
        ...other plug-in folders...
        batcher/
            ...other Batcher files and folders...
            batcher.py
    ```
3. If you have GIMP opened, you must restart GIMP.
