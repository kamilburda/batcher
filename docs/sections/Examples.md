## I don't want to preserve folder hierarchy when exporting.

Add and check the `Remove folder structure` procedure if not already (`Add Procedure... → Remove folder structure`).


## How do I rename the images to form a sequence of numbers, e.g. "image001", "image002", ...?

Click on the text entry next to `Name` and choose `image001`, or type `image[001]` in the entry.


## I want to adjust brightness in the images. Can this be done?

Yes! You may apply any GIMP filter or plug-in:
1. Select `Add Procedure... → Add Custom Procedure...`
2. Find `gimp-drawable-brightness-contrast` in the procedure browser.
3. Adjust the options as desired.
4. Select `Add` to add the procedure.


## How can I insert watermarks?

You can think of watermarks as foreground, i.e. a layer added on top of your images.

For Batch Convert and Export Images:
1. Add the `Insert foreground` procedure and specify an image file serving as the foreground.
2. (optional) You can adjust how the foreground is merged by setting the merge type in the `Merge foreground` procedure that was added automatically.

For Export Layers and Edit Layers:
1. In GIMP, assign a color tag to the layer(s) you want to consider foreground (right-click on a layer → `Color Tags` → choose your color).
2. Add the `Insert foreground` procedure and adjust the color tag as necessary.
3. (optional) For Export Layers, if you want the foreground to be offset to the current layer rather than the image canvas, place this procedure after `Resize to layer size` by dragging it onto `Resize to layer size`.
4. (optional) You can adjust how the foreground is merged by setting the merge type in the `Merge foreground` procedure that was added automatically.


## I need every image to have the same background.

You can follow the same steps as in the example above, except that you add the `Insert background` procedure (and adjust `Merge background` as needed).


## I want to create a single multipage PDF file.

While multipage PDF export is already possible in GIMP without any third-party plug-ins, Batcher allows you to apply custom procedures before the export or export each folder/group layer as separate PDFs.

1. Select or type `pdf` as the file extension.
2. Press the `Options...` button and select an option in `Perform export:`. To export a single image, select `As a single image`.
3. If you selected `As a single image`, adjust `Image filename pattern` as seen fit.
4. For Export Layers, you may want to uncheck the `Resize to layer size` procedure to use the image size (since PDF pages have the same dimensions), otherwise you might obtain unexpected results.


## I want to be able to export to multiple file formats at once.

You can achieve this by adding the `Also export as...` (or `Export`) procedure.

Each time you add this procedure, adjust the file extension, file format options and other settings as needed.


## I want to apply procedure(s) on image files (such as scaling), but I also want to export them using their original file format.

1. Press the `Options...` button and check `Use original file extension`.
2. Add and adjust your desired procedures.


## I want to export all layers using the image size, not the layer size.

Uncheck the `Resize to layer size` procedure if it exists.


## I want to export only visible layers.

Check the `Visible` constraint (or add one if not already via `Add Constraint... → Visible`).


## I want to export only visible layers. However, I also want to exclude those that have invisible parent group layers.

1. Check the `Visible` constraint (or add one if not already).
2. Edit the `Visible` constraint (press the icon to the right of the constraint name).
   In the dialog, click on `More options` and then check `Also apply to parent folders`.


## My layers contain a '.'. All characters after the '.' are replaced with the file extension. How do I prevent this?

In the text entry next to `Name`, choose `Full layer name` or type `[layer name, %e]`.
This ensures that the resulting image name will be e.g. `some.layer.png` instead of `some.png` (the default behavior).


## How do I export only group layers at the top level?

1. Uncheck the `Layers` constraint.
2. Add the `Group layers` constraint.
3. Add the `Top-level` constraint.


## How do I reverse the order of the exported images/layers?

In the text entry next to `Name`, you can type e.g. `image[000, %d]`.
This results in the exported image/layer names having a descending number.
