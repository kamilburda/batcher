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
