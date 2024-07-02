## Upcoming

New features:
* Created separate dialogs and menu entries for batch-editing layers, named `Edit Layers...` and `Edit Layers (Quick)`. Separate settings are provided for editing and exporting.

User interface changes:
* Dropdown menus are now consistently displayed below a GUI element and are left-aligned (e.g. menus displayed by pressing the `Add Procedure...` button or the `Settings` button).

Bug fixes:
* Fixed the `Rename` procedure not renaming layer groups when editing layers.
* Fixed the `Remove folder structure` procedure not working when editing layers. A separate procedure with the same name was added for editing that also allows setting the visibility of child layers based on whether all its parents are visible.
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
