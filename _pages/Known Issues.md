---
title: Known Issues
permalink: /docs/known-issues/
toc: false
---

On Windows, if you installed GIMP 3.0.0 before March 19, 2025, you will need to download and install GIMP again (or update if GIMP offers you the option). If the installer from gimp.org is not updated yet, install GIMP via Microsoft Store. There was originally an issue that prevented several plug-ins, including Batcher, from working.

If the *How to adjust file format options* export option is set to `Interactively`, and you press the Export button, it may seem as though nothing happens.
In that case, the file format dialog may be displayed behind GIMP.
If so, simply select the dialog in the taskbar to bring it up.

If you run GIMP using the official AppImage, `None` will be displayed as an option for a `Current Image`/`Current Layer` parameter in a procedure, even if the parameter does not allow omitting an image/layer. This will be fixed in a future version of GIMP.

The `C source` and `HTML` file formats require displaying a file format dialog for each image to be exported. This will be fixed in a future version of GIMP.
