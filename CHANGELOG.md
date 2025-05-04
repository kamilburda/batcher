## Upcoming

General changes:
* Added Japanese translation (thanks to @re-unknown).

Changes to procedures and constraints:
* Edit Layers: The `Selected in GIMP` constraint is now added on the first run/after reset.

Bug fixes:
* Fixed the output folder button not filling the empty space when increasing the dialog width.


## 1.0.2

### April 01, 2025

* Added Dutch translation (thanks to @DiGro).
* Updated German translation (thanks to @ChrisLauinger77).
* Fixed a crash when saving `Export`/`Also export as...` procedures (#37).
* Fixed a crash on startup if the `Pictures` user folder as the default folder is not available (#41).
* Fixed several typos in translatable strings.
* Updated installation instructions for Flatpak users.


## 1.0.1

### March 29, 2025

* Updated German translation (thanks to @ChrisLauinger77).
* Fixed a bug that caused the same custom procedure added multiple times to be saved only once. 


## 1.0

### March 19, 2025

User interface changes:
* Batch Convert: If a file is not found, an appropriate label will be displayed below the preview rather than a popup.
* Native file dialogs are displayed, if possible, when opening/saving settings files or adding files/folders for Batch Convert.

Bug fixes:
* Fixed update of settings from 1.0-RC1 to later versions.


## 1.0-RC4

### March 08, 2025

**New major feature: Export of images opened in GIMP**. You can perform image export via `File → Export Images...` or `File → Export Images (Quick)`. As with other plug-in procedures, you may make use of procedures and constraints (such as "only images with unsaved changes"). Note that this feature exports images to another file format, i.e. it does not mass-save XCF images in their original locations.

General changes:
* When exporting each image/layer individually, layers are no longer automatically merged into one. This allows preserving layers when exporting to a multi-layer format such as PSD.
* Batch Convert is now guaranteed to be accessible in GIMP even if no image is opened.

Changes to procedures:
* The `Rename` procedure is now automatically renamed based on the specified pattern (e.g. `Rename to "image[001]"`).

Bug fixes:
* Fixed a crash on startup for macOS installation packages.
* Fixed a crash in non-interactive mode if the settings file is not specified.
* Fixed a warning message displayed when exporting or editing layers of an imported (i.e. non-XCF) image.
* Fixed console warnings when opening the custom procedure browser.


## 1.0-RC3

### February 13, 2025

* Fixed Batcher not working when installed in a folder with elevated privileges (e.g. the system `plug-ins` folder containing built-in GIMP plug-ins instead of the user-specific `plug-ins` folder).


## 1.0-RC2

### February 10, 2025

General changes:
* Updated Batcher to work with GIMP 3.0.0-RC3. **Due to backwards-incompatible changes, Batcher now requires GIMP 3.0.0-RC3 or later**. Saved settings from previous versions will still work properly.
* You can now choose `None` for image and layer arguments in custom procedures if a procedure allows omitting them.
* More appropriate GUI is displayed for settings and procedure arguments representing files or folders. You can also choose to omit these arguments if a procedure allows omitting them.
* For `Gimp.Unit` procedure arguments, the pixel and/or percentage units are not shown if a procedure is set to hide them.

Bug fixes:
* Fixed settings from version 0.8 not being updated to 1.0-RC1 and later.
* Fixed a potential bug where arrays of images, layers and other GIMP objects as procedure or constraint arguments could not be edited.


## 1.0-RC1

### January 22, 2025

**New major feature: Batch conversion of files.** You can now batch-process image files and convert them to a different file format, optionally applying procedures (scale, insert background, ...) and filtering the list of images to be processed via constraints (filenames having a particular file extension, beginning/ending with a prefix/suffix, ...).

Changes to procedures and constraints:
* Added a new procedure named `Align and offset` that allows aligning layer(s) with the image or another layer. You may also apply offsets with pixels or a percentage of image/layer width/height.
* For the `Scale` procedure, you may now choose whether to scale a layer (the default for Export Layers and Edit Layers) or the entire image (a new option, the default for Batch Convert).
* Renamed `Use layer size` to `Resize to layer size` and allowed customizing the layer. You may now resize the background layer, foreground layer or all layers (the latter effectively resizing the image to fit all layers).
* Added `Merge filters` as a built-in procedure that merges all visible filters (layer effects) in the specified layer. This is equivalent to adding the `gimp-drawable-merge-filters` procedure, only more convenient.
* Added a new constraint named `Matching text...` that allows filtering items that start with, contain or end with the specified text. You may also specify a Python regular expression or perform case-insensitive matching. The name of the constraint automatically changes as you adjust its options.
* The `Use file extension in layer name` option for the `Export` procedure now uses the original layer name. This way, you no longer need to specify the `[full layer name]` field just to preserve the file extension. This also allows using different name patterns that do not include the layer name (such as `image[001]`).
* Procedures and constraints causing errors are now automatically deactivated. This avoids spamming the user with warning dialogs.

User interface changes:
* Replaced the placeholder icon in the image preview when there is no selection.
* Labels describing procedure/constraint parameters are now insensitive (grayed out) if their corresponding GUI elements are insensitive.
* Export settings are now insensitive while exporting.

Other changes:
* When running Batcher non-interactively, the `settings-file` parameter is now a string rather than a `GFile` object for convenience.

Bug fixes:
* Fixed warnings issued by GIMP when adding or applying layer effects as custom procedures.
* Fixed the `Rename` procedure not working for Edit Layers.


## 0.8.2

### December 29, 2024

* Fixed GIMP plug-ins being displayed in the wrong category in the custom procedure browser.


## 0.8.1

### December 29, 2024

User interface changes:
* Dialogs for editing procedures, constraints and export settings are now scrollable if exceeding a certain height. Some custom procedures (e.g. `gegl:styles`) and file formats (e.g. DDS) have a large number of parameters, which previously made the dialogs too high to fit the screen.
* Increased the minimum width of labels in dialogs. This makes particularly the procedure browser dialog more readable.

Bug fixes:
* Fixed visually unappealing borders in the custom procedure browser appearing when switching to a procedure requiring scrolling.
* For Export Layers, fixed the wrong name for the `Cancel`/`Close` button on plug-in startup if `Close When Done` is unchecked.


## 0.8

### December 28, 2024

General changes:
* Updated Batcher to work with GIMP 3.0.0-RC2. **Due to backwards-incompatible changes, Batcher now requires GIMP 3.0.0-RC2 or later**. Saved settings from previous versions will still work properly.

New features:
* Non-destructive layer effects (filters, GEGL operations) can now be added as custom procedures. They can be found under the `Filters, Effects` category in the custom procedure browser. Beside parameters specific to each effect, you can adjust their blend mode, opacity, or they can optionally be merged into the layer (i.e. applied destructively).
* You may now attempt to apply a procedure to multiple layers at once using the new `All Layers` option, if available for a particular procedure (usually those having the `The input drawables` argument). Note that a procedure may still fail even if this option is available as it may not support working with multiple layers at once.
* Rename procedure: Added a new field named `[output folder]` that allows inserting the output folder selected in the plug-in dialog. You can adjust the path components to be inserted as well as the separator and wrapper around each component (in the same vein as `[layer path]`).
* Rename procedure: Added `%n` option to the `[layer name]` and `[layer path]` fields acting as the inverse of `%i`.

Changes to procedures and constraints:
* Removed the `Selected in preview` constraint. For Export Layers and Edit Layers, the `Selected in GIMP` and `With color tags` constraints already provide a good equivalent.
* Rename procedure: For the `[attributes]` field, changed the layer attributes from `%w`, `%h`, `%x` and `%y` to `%lw`, `%lh`, `%lx` and `%ly`, respectively.

User interface changes:
* Increased the width of the procedure browser so that there is more space to display labels for layer effects without the labels spanning too many lines.
* Added a small delay to the image preview when the selected item changes. This prevents excessive changes when the selection changes rapidly.
* Optimized the update of input items (when items are added/removed/renamed/updated upon changing procedures or constraints) if many items (hundreds and more) are present.
* For Export Layers and Edit Layers, moved the "Preview" label directly above the image thumbnail and added a label named "Input Layers" above the list of layers.
* Simplified how the preview is created internally, removing steps such as downscaling or merging layers.

Bug fixes:
* Fixed Export/Edit Selected Layers not working for group layers.
* Fixed export for procedures manipulating image dimensions, selection and other image-wide attributes (such as `script-fu-addborder`, `script-fu-circuit` or conversion to the indexed type).
* Fixed occasional artifacts in the preview.
* Fixed the preview not working correctly for group layers.
* Fixed constraints incorrectly excluding items in the preview. The bug caused items e.g. matching the `Matching File Extension` constraint to be excluded from the preview as its name may have changed during processing.
* Fixed occasional incorrect names in the preview under the image thumbnail.
* Fixed the `Rename` procedure renaming folders after items if `Rename folders` is enabled.
* Fixed the `Rename` procedure assigning incorrect descending numbers if `Rename folders` is enabled.
* Fixed a crash on plug-in startup if a file format is no longer available.
* Fixed loading settings related to layers (e.g. layers selected in the preview) whose names contain `/`.


## 0.7

### December 07, 2024

* Added `Scale to fit` and `Keep aspect ratio` options to the Scale procedure.


## 0.6

### November 18, 2024

* Updated Batcher to work with GIMP 3.0.0-RC1. **Batcher now requires GIMP 3.0.0-RC1 or later.** Earlier development versions of GIMP (2.99.x) will not work. Any future GIMP 3.x version will work unless stated otherwise.
* Greatly optimized the preview when changing selection. The performance drop was noticeable for hundreds of items.
* Fixed several bugs related to the preview when the selected item is changed.
* Fixed `Insert background` and `Insert foreground` procedures inserting group layers twice.
* Fixed occasional GIMP error messages when batch processing is finished.


## 0.5

### October 12, 2024

Changes to the export settings:
* Added a button named `Options...` in the main dialog to adjust options previously only available when adding the `Export` procedure.
* Rearranged export settings horizontally, both in Export Layers and Export Layers (Quick).
* Renamed `Save in Folder` to `Folder` and `Save As` to `Name` for brevity.
* The native file format dialog is no longer displayed by default. File format options are now adjusted in the export options (displayed by pressing the `Options...` button). This behavior can be toggled back if desired, particularly when you need to choose the image metadata to preserve (this can currently be adjusted only via native file format dialogs).
* By default, when a file about to be exported already exists with the same name, the new file will be renamed. This was inconsistent previously (e.g. when running non-interactively, the default was to skip the new files).
* The default export folder is now the `Pictures` user folder instead of `Documents`.
* The file extension is now validated automatically. An invalid file extension is automatically reverted to the last valid value instead of displaying warnings.
* The overwrite prompt is now displayed in Edit/Export Layers (Quick) if `Show This Dialog` is checked.

Changes to the `Export` procedure:
* For Export Layers, the `Export` procedure now performs additional export instead of overriding the default export. The procedure name for Export Layers is now `Also export as...` to reflect this change. The name changes automatically as you modify the file extension (e.g. `Also export as PNG` if the file extension is `png`).
* For Export Layers, when the `Export` procedure is added, values of the options are copied from the default export (e.g. the output folder will be identical to the one currently selected in the main dialog).
* Add a new option `If a file exists:` that allows skipping the dialog asking the user to handle existing files and setting a fixed mode for all files.
* Removed the `Preserve layer name after export` option. The layer name is now always preserved.

Other changes:
* The `Rename` procedure for Export Layers now performs renaming on top of the default renaming (the text entry next to `Name`) instead of overriding it.
* File load and file save procedures can no longer be added as custom procedures due to being redundant (loading a file would have no effect and file save procedures are already covered by the `Export` procedure).
* The plug-in no longer crashes if the automatic update of plug-in settings to the latest version fails. Instead, the settings are reset.

Bug fixes:
* Fixed unchangeable file extension in Export Layers (Quick).
* Fixed overwrite prompt not being displayed for `Export` procedures for Edit Layers.
* Fixed a crash when starting the plug-in if text layer(s) were selected in the preview and plug-in settings were saved.
* Fixed a crash when in-dialog warning messages were displayed on plug-in startup (e.g. if the plug-in was saved with an ill-formatted file extension).
* Removed the "Flatten" option from `Merge Back-/Foreground` as it was unsupported and caused merging to fail.


## 0.4

### July 13, 2024

New features:
* Created separate dialogs and menu entries for batch-editing layers, named `Edit Layers...` and `Edit Layers (Quick)`. Separate settings are provided for editing and exporting.
* Added `Export Selected Layers` and `Edit Selected Layers` menu entries when right-clicking on selected layers in GIMP. These behave as Export Layers (Quick) and Edit Layers (Quick), respectively, except that only `Layers` and `Selected in GIMP` constraints apply.
* Added a new layer name pattern called `Full layer name` which preserves the entire layer name, including characters beyond the last '.'. This is equivalent to `[layer name, %e]`, only more convenient.

Changes to procedures and constraints:
* Simplified the insertion of background and foreground. The `Merge background`/`Merge foreground` procedure is added automatically and is no longer available to be added manually. A constraint named `Not background`/`Not foreground` is also added automatically that ignores the background/foreground during processing. Updating the color tag in the `Insert background`/`Insert foreground` procedure also updates the color tag in the constraint.
* Added back the `Visible` constraint displayed on the first run/after reset. This was removed in the previous version; this time, however, `Also apply to parent folders` is not checked by default.

User interface changes:
* When `Export Layers (Quick)` is run for the first time, a small dialog with only export settings is now displayed. This reduces confusion as to where (output folder) and how (file extension, name pattern) the layers are exported. That dialog can be skipped by simply unchecking `Show this dialog`.
* Dropdown menus are now consistently displayed below a GUI element and are left-aligned (e.g. menus displayed by pressing the `Add Procedure...` button or the `Settings` button).
* Renamed `Import Settings...` to `Load Settings from File...` and `Export Settings...` to `Save Settings to File...` for clarity, respectively.
* Moved `Reset Settings` menu entry under the `Settings` button to the bottom.
* Closing the main dialog automatically can be turned on/off via the new `Close when Done` menu under the `Settings` button.

Bug fixes:
* Fixed the `Rename` procedure not renaming layer groups when editing layers.
* Fixed the `Remove folder structure` procedure not working when editing layers. A separate procedure with the same name was added for editing that also allows setting the visibility of child layers based on whether all its parents are visible.
* Fixed the `Scale` procedure throwing errors if the resulting width or height would be 0 pixels. The new width and height will now always be at least 1 pixel.
* Fixed the `Selected in GIMP` constraint applying only on a single layer when editing layers.
* Fixed incorrect progress bar text if the user chose the new file to be renamed (to avoid overwriting a file with the same name).


## 0.3

### June 17, 2024

Redesigned user interface:
* Replaced the folder chooser widget with a folder chooser button.
* Procedures and constraints are now aligned vertically.
* Adjusting settings for procedures and constraints now immediately updates the preview for improved feedback and interactivity.
* Multiple edit dialogs (one for each procedure/constraint) can now be displayed simultaneously.
* Edit dialogs for procedures and constraints are no longer separate windows and are hidden/shown simultaneously with the main dialog.
* Completely reworked the custom procedure browser. You may now preview and tinker with a procedure/plug-in/script directly from the browser dialog before adding it to the list of procedures permanently.
* In edit dialogs, replaced PDB parameter names with human-readable descriptions where available. The names are displayed as tooltips in case a user wants to track down issues with a procedure.
* Moved detailed information about a procedure/constraint from a tooltip to a button showing a popup.
* Given the changes above, adjusted dialog dimensions, positions of separators and spacing/margins/border width.

Bug fixes:
* Added executable bit to the main `batcher.py` file. This could otherwise prevent the plug-in from being registered (i.e. from appearing in GIMP) on Unix-like platforms.
* Fixed a crash for PDB procedures containing GIMP resources (brushes, palettes, gradients, patterns) as settings.
* Prevented errors for PDB procedures with array arguments requiring a non-zero number of elements (e.g. pencil).
* Fixed an issue where color parameters for some PDB procedures could not be adjusted.
* Fixed redundant preview updates when the main, edit or procedure browser dialogs (re)gained focus.

Other changes:
* Renamed the `Export Layers Now` menu entry to `Export Layers (Quick)` for hopefully greater clarity.


## 0.2

### February 21, 2024

* Updated Batcher to work with GIMP 2.99.18. Due to backwards incompatible changes, Batcher will no longer work with GIMP 2.99.16 and below.
* Moved menu entries to the section containing `Export...` and `Export As...`. 
* Fixed translations not working.
* Fixed incorrect URLs to the help page when pressing the Help button.


## 0.1

### January 31, 2024

* Initial release.
