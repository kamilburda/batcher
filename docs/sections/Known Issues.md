On Windows, if you downloaded GIMP 3 before March 19, 2025, you will need to update GIMP (or download and install GIMP again if GIMP does not offer an update). There was originally an issue that prevented several plug-ins, including Batcher, from working.

If the *How to adjust file format options* export option is set to `Interactively`, and you press the Export button, it may seem as though nothing happens.
In that case, the file format dialog may be displayed behind GIMP.
If so, select the dialog in the taskbar to bring it up.

For the `Color Correction` action, Batcher currently supports applying levels or curves in the linear mode only. If you saved your preset in a different mode (e.g. non-linear or perceptual), the action will fail with a warning dialog.

For Batch Convert, import options for unrecognized file formats cannot be adjusted and default values will be used.

If some actions result in errors, notably layer effects, the error message provided by Batcher is rather generic or there is none. A more detailed error message, if any, can be displayed in GIMP via `Windows → Dockable Dialogs → Error Console`. In previous Batcher versions, these messages were displayed as separate popups - however, these popups were often displayed repeatedly and kept obscuring the Batcher dialog.

Images created by custom actions (e.g. via `plug-in-decompose`) are currently not usable in Batcher.
[This will be resolved in a future version](https://github.com/kamilburda/batcher/issues/56).

If you run GIMP using the official AppImage, `None` will be displayed as an option for a `Current Image`/`Current Layer` parameter in an action, even if the parameter does not allow omitting an image/layer. This will be fixed in a future version of GIMP.

The `C source` and `HTML` file formats require displaying a file format dialog for each image to be exported. This will be fixed in a future version of GIMP.
