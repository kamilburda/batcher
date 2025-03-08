---
title: Procedures
permalink: /docs/procedures/
---

Procedures allow you to apply image filters to each image/layer.
Press the `Add Procedure...` button and select one of the available procedures, or add a [custom procedure](#adding-custom-procedures).

For each procedure, you may:
* enable/disable the procedure,
* move the procedure up/down by dragging the procedure with mouse or by pressing Alt + Up/Down on your keyboard,
* [edit the procedure](Editing Procedures and Constraints.md),
* remove the procedure.

You can add the same procedure multiple times.


## Built-in Procedures

### Align and offset

Aligns layer(s) with the current image or, if specified, another layer within the image.
You may specify additional offsets after the alignment is applied.

Options:
* *Layers to align*: Layers to align. This can be a single layer (e.g. the current layer, background, foreground) or all layers inserted in the currently processed image.
* *Object to align layers with*: Whether to align with the entire image or another layer.
* *Another layer to align layers with*
* *Horizontal alignment*: Left, center or right alignment, or *Keep* the horizontal position intact.
* *Vertical alignment*: Top, center or bottom alignment, or *Keep* the vertical position intact.
* *Additional X-offset*: Moves the layers horizontally by the specified amount.
* *Unit for the additional X-offset*: Can be pixels or percentages of image/another layer width/height.
* *Additional Y-offset*: Moves the layers vertically by the specified amount.
* *Unit for the additional Y-offset*: Can be pixels or percentages of image/another layer width/height.

### Export**/**Also export as...

Exports an image/layer to the specified file format.

For Batch Convert and Export Layers, this performs export to another file format.

You can add this procedure multiple times to export to multiple file formats at once.

Options:
* *Output folder*: Folder to export the output image(s) to.
* *File extension*: File extension of the output image(s).
* All options specified in [Export Options](Export Options.md).

The name of the Export procedure is automatically updated as you modify the file extension.

For Batch Convert and Export Layers, when this procedure is added, the values of the options are copied from the default export options.
For example, the output folder will be identical to the one currently selected in the main dialog.
This simplifies setting up export to multiple file formats without the hassle of manually adjusting the export options in all added procedures.

When exporting each image separately (the default, which can be changed via the *Perform export* option), the Export procedure usually makes sense to be applied as the last procedure since procedures after Export would have no effect on the current layer being processed.

### Apply opacity from group layers

*Only available for: Export Layers, Edit Layers*

Combines opacity from all parent group layers for each layer.
This corresponds to how the layer is actually displayed in GIMP.

For example, if a layer has 50% opacity and its parent group also has 50% opacity, the resulting opacity of the layer will be 25%.

### Insert background

Inserts a new layer behind the current layer.

For Batch Convert, specify an image file to be loaded as background.

For Export Layers and Edit Layers, mark layers in your opened image with a color tag.
The _blue_ color tag is used for background by default.
You may set a different color tag by adjusting the `Color tag` option.

This procedure is inserted at the first position.
This prevents potential confusion when `Resize to layer size` is not present and the background is offset relative to the layer rather than the image canvas.
If this is your intention, you can always move this procedure below `Resize to layer size`.

The background is merged automatically at the end of processing as the `Merge background` procedure is automatically added. See `Merge background` below for more information.

For Export Layers and Edit Layers, the background layers are excluded from processing by default as the `Not background` constraint is automatically added and enabled.

### Insert foreground

Inserts a new layer in front of the current layer.

For Export Layers and Edit Layers, the _green_ color tag is used as foreground by default.

The `Merge foreground` procedure is added automatically. For Export Layers and Edit Layers, the `Not foreground` constraint is added automatically.

For more information, see `Insert background` above.

### Merge background

*Only available if `Insert background` is added*

Merges already inserted background (via `Insert background`, see above) into the current layer.

When exporting, the background is merged automatically.
However, if needed, you can reorder this procedure to perform the merge earlier and then apply procedures on the current layer, now merged with the background.

For [Edit Layers](../Usage.md#editing-layers), this procedure ensures that you have a single merged layer rather than having the background as a separate layer.
If this is not what you desire, you may uncheck this procedure.

If there is no background layer inserted, this procedure has no effect.

Options:
* *Merge type*: Indicates how to perform the merge. The available merge types are the same as for [Merge Visible Layers](https://docs.gimp.org/2.10/en/gimp-image-merge-layers.html), under the section `Final, Merged Layer should be:`.

### Merge foreground

*Only available if `Insert foreground` is added*

Merges already inserted foreground (via `Insert foreground`, see above) with the current layer.

For more information, see `Merge background` above.

### Merge filters

Merges all visible filters (layer effects) in the specified layer.

### Merge visible layers

*Only available for: Batch Convert, Export Images*

Merges all visible layers within the image into a single layer. Invisible layers are removed.

This is useful if the image contains multiple layers and you want to apply filters (layer effects) or other procedures on the entire image.

### Remove folder structure

*Only available for: Batch Convert, Export Layers, Edit Layers*

Exports all images to the output folder on the same level, i.e. subfolders are not created.

Options:
* (Edit Layers only) *Consider visibility of parent folders*: If checked, a layer will become invisible if any of its parents are not visible (even if the layer itself is visible). Having this checked corresponds to how the layers are displayed in the image canvas.

### Rename

Renames images/layers according to the specified pattern.

This procedure uses the same text entry as the one in Batch Convert or Export Layers next to `Name`, described in [Renaming](Renaming.md).

For Batch Convert and Export Layers, this procedure performs renaming on top of the entry next to `Name`.

Additionally, this procedure allows customizing whether to rename both images/layers and folders (by checking `Rename folders`/`Rename group layers`) or rename folders only (by checking `Rename folders`/`Rename group layers` and unchecking `Rename images`/`Rename layers`).

### Resize to layer size

*Only available for: Batch Convert, Export Images, Export Layers*

If enabled, the image canvas will be resized to fit the layers. For Export Layers, this means that the exported image will have the same dimensions as the layer to export.

This procedure is enabled by default for Export Layers.

To keep the image canvas intact (thus keeping the layer position within the image), uncheck this procedure.
Note that in that case the layers will be cut off if they are partially outside the image canvas.

### Scale

Scales the entire image or a layer, using absolute (pixels) or relative (percentages) measures.

Options:
* *Image*: Image to scale and/or to use for computing the new width or height.
* *Layer*: Layer to scale and/or to use for computing the new width or height.
* *Object to scale*: Whether to scale the entire *Image* or the *Layer* within the image.
* *New width*: The new width.
* *Unit for width*: Unit for the new width - pixels or percentages of image/layer width/height.
* *New height*: The new height.
* *Unit for height*: Unit for the new height - pixels or percentages of image/layer width/height.
* *Interpolation*: Type of interpolation to use.
* *Use local origin*: If checked and *Object to scale* is set to *Layer*, the layer will be scaled around its center. If not checked, the layer will be placed to the upper left corner of the image.
* *Scale to fit*: If checked, the image/layer will be scaled such that it fits *New width* or *New height*, whichever is smaller, while also preserving the aspect ratio. You can imagine a canvas having the dimensions *New width* and *New height* to which the image/layer will be fit.
* *Keep aspect ratio*: If checked, the image/layer is scaled such that the ratio between the width and height is preserved. You can choose the dimension to be fixed via the *Dimension to keep* option.
* *Dimension to keep*: The dimension - width or height - to be considered fixed when scaling with the *Keep aspect ratio* option checked.


## Adding Custom Procedures

You can add any GIMP plug-in, layer effect (filter, GEGL operation) or GIMP procedure by pressing `Add Procedure...` and then selecting `Add Custom Procedure...`. Both built-in and any third-party plug-ins and layer effects are supported.

![Procedure browser dialog](../../assets/images/screenshot_procedure_browser_dialog.png){: .align-center}

You can preview how the selected procedure affects the resulting image (by pressing `Preview`) and adjust procedure options.

Once you are settled on the procedure, press `Add` to permanently add it to the list of procedures.
You can [edit the procedure](Editing Procedures and Constraints.md) anytime after adding it.

All layer effects (procedures under the `Filters, Effects` category) have the following common parameters:
* *Blend mode* - blend mode for the effect (default, dodge, burn, hard light, ...).
* *Opacity* - the opacity of the effect.
* *Merge filter* - the effect will be applied destructively, i.e. will be merged into the layer.
* *Visible* (displayed under `More options`) - if unchecked, the effect will be added, but will not be applied.
* *Filter name* (displayed under `More options`) - a custom name for the effect. If empty, a default name is assigned by GIMP.
