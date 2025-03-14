If the *How to adjust file format options* export option is set to `Interactively`, and you press the Export button, it may seem as though nothing happens.
In that case, the file format dialog may be displayed behind GIMP.
If so, simply select the dialog in the taskbar to bring it up.

If you run GIMP using the official AppImage, `None` will be displayed as an option for a `Current Image`/`Current Layer` parameter in a procedure, even if the parameter does not allow omitting an image/layer. This will be fixed in a future version of GIMP.

The following file formats require displaying a file format dialog for each image to be exported:
* C source,
* HTML.

On Windows, exporting with the following file formats does not work properly if file paths contain accented (Unicode) characters:
* X PixMap Image.
