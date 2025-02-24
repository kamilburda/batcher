---
title: Constraints
permalink: /docs/constraints/
---

To exclude certain images/layers from processing and export, press the `Add Constraint...` button and select one of the available constraints.

Just like [procedures](Procedures.md), you may enable/disable, reorder, [edit](Editing Procedures and Constraints.md) or remove constraints.


## Built-in Constraints

### Layers

*Only available for: Export Layers, Edit Layers*

Processes only layers (i.e. group layers are not processed).

### Group layers

*Only available for: Export Layers, Edit Layers*

Processes only group layers.

You need to disable the `Layers` constraint since having both enabled will result in no layer being processed.

### Not background

*Only available for: Export Layers, Edit Layers*

*Only available if `Insert background` is added*

Processes only layers that are not inserted as background via `Insert background`.

### Not foreground

*Only available for: Export Layers, Edit Layers*

*Only available if `Insert foreground` is added*

Processes only layers that are not inserted as foreground via `Insert foreground`.

### Matching file extension

Processes only images/layers having the file extension typed in the main dialog.

### Matching text...

Processes only images/layers matching the specified text.

You can adjust how to perform matching - whether the image/layer name should start with, contain or end with the specified text to match. For example, with the "Ends with text" option, you can match against an arbitrary file extension instead of the one typed in the main dialog (via the `Matching file extension` constraint).

Matching can be made case-insensitive by checking the *Ignore case sensitivity* option.

You can also specify a regular expression pattern as defined in the [`re` module for Python](https://docs.python.org/3/library/re.html). Errors in the regular expression pattern will result in no matches.

### Recognized file format

*Only available for: Batch Convert*

Processes only images whose original file extension is supported by GIMP.

If you use third-party file load plug-ins with their own file extension, uncheck this constraint so they can be processed.

### Selected in GIMP

*Only available for: Export Layers, Edit Layers*

Processes only layers selected in GIMP.

### Top-level

Processes only top-level images/layers (i.e. images/layers inside any folder/group layer are excluded).

### Visible

*Only available for: Export Layers, Edit Layers*

Processes only visible layers.

### With color tags

*Only available for: Export Layers, Edit Layers*

Processes only layers having a color tag.

By default, all layers without a color tag are excluded.
To process only layers with specific color tags, edit this constraint and add the color tags for the `Color tags` option.
For example, by adding a blue tag, only layers containing the blue tag will be processed.
Other tagged or untagged layers will be excluded.

### Without color tags

*Only available for: Export Layers, Edit Layers*

Processes only layers without a color tag.

By default, all layers with a color tag are excluded.
To exclude only specific color tags, edit this constraint and add the color tags for the `Color tags` option.
For example, by adding a blue tag, all layers except the ones containing the blue tag will be processed.

If a group layer has a color tag, it will normally not be excluded.
To also exclude group layers with color tags, click on `More options` and check `Also apply to parent folders`.
