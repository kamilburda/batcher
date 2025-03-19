## Requirements

On Windows, Batcher requires [GIMP 3.0.0-RC3](https://download.gimp.org/gimp/v3.0/windows/gimp-3.0.0-RC3-setup.exe). **Batcher currently does not work with GIMP 3.0.0 due to an issue in GIMP.**

On Linux and macOS, Batcher requires [GIMP 3.0.0](https://www.gimp.org/downloads/) or later.

If you installed GIMP from an unofficial package, you might need to install Python 3.7 or later.


## Download

Batcher can currently be installed only manually by copying files from a ZIP archive.

**[Download latest release](https://github.com/kamilburda/batcher/releases/tag/{% include-config 'PLUGIN_VERSION' %}) ({% include-config 'PLUGIN_VERSION' %}, {% include-config 'PLUGIN_VERSION_RELEASE_DATE' %})**


## Windows

1. Make sure you install [GIMP 3.0.0-RC3](https://download.gimp.org/gimp/v3.0/windows/gimp-3.0.0-RC3-setup.exe). **Batcher currently does not work with GIMP 3.0.0.**
2. Make sure you have GIMP installed with support for Python plug-ins.
3. Locate the folder containing GIMP plug-ins - open GIMP and go to `Edit → Preferences → Folders → Plug-Ins`. If you cannot locate any of the folders on your system, you can add a custom folder. 
4. Copy the `batcher` folder from the downloaded archive to one of the folders chosen in the previous step. The folder hierarchy should look like this:
    ```
    plug-ins/
        ...other plug-in folders...
        batcher/
            ...other Batcher files and folders...
            batcher.py
    ```


## Linux

1. Locate the folder containing GIMP plug-ins - open GIMP and go to `Edit → Preferences → Folders → Plug-Ins`. If you cannot locate any of the folders on your system, you can add a custom folder. 
2. Copy the `batcher` folder from the downloaded archive to one of the folders chosen in the previous step. The folder hierarchy should look like this:
    ```
    plug-ins/
        ...other plug-in folders...
        batcher/
            ...other Batcher files and folders...
            batcher.py
    ```


## macOS

1. Locate the folder containing GIMP plug-ins - open GIMP and go to `Edit → Preferences → Folders → Plug-Ins`. If you cannot locate any of the folders on your system, you can add a custom folder. 
2. Copy the `batcher` folder from the downloaded archive to one of the folders chosen in the previous step. The folder hierarchy should look like this:
    ```
    plug-ins/
        ...other plug-in folders...
        batcher/
            ...other Batcher files and folders...
            batcher.py
    ```
