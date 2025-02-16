Export options are available upon pressing the `Options...` button (if available), or when adding the `Export`/`Also export as...` procedure.

* *How to adjust file format options*: If set to `Interactively`, a native file format dialog is displayed for the first image to be exported. If set to `Use options below` (the default), you can adjust file format options in place without showing a file format dialog.
* *File format options*: A list of options specific to the file format typed in the main dialog.
* *If a file exists*: If set to `Ask` (the default), the user is asked to choose how to handle existing files (replace, skip, rename, etc.). Setting this to a different value applies that mode to each file without asking the user (e.g. setting this to `Replace` will automatically replace all existing files with the same name).
* *Perform export*: Whether to export each item separately ("For each image"/"For each layer"), each top-level item or folder separately ("For each top-level image or folder"/"For each top-level layer or group"), or a single image containing all items ("As a single image").
  The latter two options provide multi-layer export. This allows exporting e.g. multipage PDFs or animated GIFs with additional custom procedures applied before the export.
* *Image filename pattern*: Filename pattern available when a single image is exported (the "Entire image at once" option is selected).
  The text entry next to `Name` still applies to individual layer names (since some multi-layer file formats also store layer names, e.g. TIFF or PSD).
* *Use original file extension*/*Use file extension in layer name*: If an image/layer name has a recognized file extension, use that file extension in place of the default file extension. Note that, currently, the only way to adjust file format options for each different file format is to set *How to adjust file format options* to `Interactively`.
* *Convert file extension to lowercase*: File extensions in layer names are converted to lowercase.
* *Use original modification date* (Batch Convert only): Preserves the original access and modification dates.
