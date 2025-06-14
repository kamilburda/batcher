On Windows, if you downloaded GIMP 3 before March 19, 2025, you will need to update GIMP (or download and install GIMP again if GIMP does not offer an update). There was originally an issue that prevented several plug-ins, including Batcher, from working.

If the *How to adjust file format options* export option is set to `Interactively`, and you press the Export button, it may seem as though nothing happens.
In that case, the file format dialog may be displayed behind GIMP.
If so, select the dialog in the taskbar to bring it up.

For the `Color Correction` action, Batcher currently supports applying levels or curves in the linear mode only. If you saved your preset in a different mode (e.g. non-linear or perceptual), it will still be applied as if the mode was set to linear.

Some layer effects (filters, GEGL operations) can only be applied destructively. If you add such an effect as an action, you will obtain an error message saying the effect cannot be applied non-destructively. This is a limitation of the effect itself, and Batcher currently does not detect whether a layer effect can be applied destructively or not. To avoid the error message, check `Merge filter`.

If you run GIMP using the official AppImage, `None` will be displayed as an option for a `Current Image`/`Current Layer` parameter in an action, even if the parameter does not allow omitting an image/layer. This will be fixed in a future version of GIMP.

The `C source` and `HTML` file formats require displaying a file format dialog for each image to be exported. This will be fixed in a future version of GIMP.
