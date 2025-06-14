To edit an [action](Actions.md) or a [condition](Conditions.md), press the icon to the right of the action/condition name and adjust the options in the displayed dialog.

The dialog will be automatically displayed for most [built-in actions](Actions.md#built-in-actions) and some [built-in conditions](Conditions.md#built-in-conditions) when added.

## Placeholder Values

If an action or condition contains an image or a layer argument, you will be offered to select a "placeholder" - a value that is determined during processing.

For image arguments, you may select one of the following:
* `Current Image` (default): the currently processed image.
* `None`: ignores the image. Only available if an action/condition allows omitting it (i.e. if the image is optional).

For layer/drawable/item arguments, you may select one of the following:
* `Current Layer` (default): the currently processed layer. For Batch Convert, an input image usually contains a single layer, which will be considered the current layer. In case of multi-layer images, the first layer is considered, or the first selected layer if the stored image file contains information on the selected layers (e.g. XCF or PSD).
* `Layer Below (Background)`: a layer placed directly after `Current Layer`, representing background. This layer is inserted via the `Insert background` action or by a custom action. If there is no such layer, the entire action/condition will be skipped.
* `Layer Above (Foreground)`: a layer placed directly before `Current Layer`, representing foreground. This layer is inserted via the `Insert foreground` action or by a custom action (e.g. `gimp-text-font` which renders a text layer). If there is no such layer, the entire action/condition will be skipped.
* `None`: ignores the layer. Only available if an action/condition allows omitting it (i.e. if the layer is optional).
* `All Layers`: applies the action/condition to all layers within the currently processed image. This option is available usually only for actions/conditions having the `The input drawables` argument. Note that an action/condition may not work on multiple layers at once and thus may yield an error if this option is chosen.

For several built-in actions (such as `Scale` or `Rotate and flip`), numeric arguments representing dimensions, coordinates, etc. can be specified in a variety of units, such as pixels, percentages (e.g. of width of the current image), inches and others. Percentages are converted to pixels. Inches and other units are converted to pixels based on the current image's resolution (in case of Edit Layers and Export Layers, the image of the processed layer).


## More Options

Expanding `More options` allows you to adjust the options below.

### Enable for previews

If checked (the default), the action/condition is applied in the preview.
Unchecking this can be useful if an action takes too long.

### Also apply to parent folders

*Only available for conditions*

If checked, an image/layer will satisfy a condition if all of its parent folders/group layers also satisfy the condition.
For example, if this option is checked for the `Visible` condition, a visible layer is excluded if any of its parent group layers are not visible.
