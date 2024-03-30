## Upcoming

Redesigned user interface:
* Replaced the folder chooser widget with a folder chooser button.
* Procedures and constraints are now aligned vertically.
* Adjusting settings for procedures and constraints now immediately updates the preview for improved feedback and interactivity.
* Multiple edit dialogs (one for each procedure/constraint) can now be displayed simultaneously.
* Edit dialogs for procedures and constraints are no longer separate windows and are hidden/shown simultaneously with the main dialog.
* Moved detailed information about a procedure/constraint from a tooltip to a button showing a popup.
* Given the changes above, adjusted dialog dimensions, positions of separators and spacing/margins/border width.

Bug fixes:
* Fixed a crash for PDB procedures containing GIMP resources (brushes, palettes, gradients, patterns) as settings.
* Prevented errors for PDB procedures with array arguments requiring a non-zero number of elements (e.g. pencil).
* Fixed redundant preview update when the main dialog (re)gained focus.

Other changes:
* Moved menu entries back under the `Batch` submenu to avoid confusion with the `Export...` and `Export As...` menu entries.


## 0.2

### February 21, 2024

* Updated Batcher to work with GIMP 2.99.18. Due to backwards incompatible changes, Batcher will no longer work with GIMP 2.99.16 and below.
* Moved menu entries to the section containing `Export...` and `Export As...`. 
* Fixed translations not working.
* Fixed incorrect URLs to the help page when pressing the Help button.


## 0.1

### January 31, 2024

* Initial release.
