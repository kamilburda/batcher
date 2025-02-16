Batcher offers renaming each image/layer using several built-in *fields*.
For example, `image[001]` renames the images/layers to `image001`, `image002` and so on. You can combine multiple fields, for example `[layer name]-[001]`.

Renaming is available via the text entry next to `Name` or via the `Rename` procedure.
Press the Down button or click anywhere on the entry to display the list of available fields.
The text entry can show you examples of how each field is used if you place the text cursor inside a field (e.g. inside `[001]`).

The input list of images/layers automatically updates as you change the name pattern and so can greatly help you figure out how your specified pattern affects the image/layer names.

Fields must be enclosed in square brackets and must have a correct number of options.
Options must be separated by commas (`,`).
Invalid options result in the field being inserted literally.

## Available fields

You can choose the fields from the dropdown list displayed when clicking on the text entry, or you can type the fields manually.

### Number

A number incrementing for each image/layer.
The numbering is separate for each folder/group layer.

Options:
* `%n`: Continue numbering across folders/group layers.
* `%d<number>`: Use descending numbers, optionally with the specified padding (number of digits).
  If the number is 0, the first number is the number of images/layers to export within a folder/group layer, or, if `%n` is also specified, the number of all images/layers to export.

Examples:
* `[1]` → `1`, `2`, ...
* `[001]` → `001`, `002`, ..., `009`, `010`, ..., `999`, `1000`, ...
* `[005]` → `005`, `006`, ...
* `[001, %n]` → `001`, `002`, ... (continues numbering across folders/group layers)
* `[000, %d]` → `010`, `009`, ... (if the number of layers is 10)
* `[10, %d2]` → `10`, `09`, ...

### \[image name\]

The current image name.

Options:
* *file extension strip mode*:
	* `%e`: Never strip the extension.
	* `%i` (Batch Convert only): Strip the extension only if the image has a file extension that does not match the entered file extension.
	* `%n` (Batch Convert only): Strip the extension only if the image has a file extension that matches the entered file extension (the inverse of `%i`).

Examples:
* `[image name]` for an image named `Frame` → `Frame`
* `[layer name]` for an image named `Frame.png` → `Frame`
* `[image name, %e]` for an image named `Frame.png` if the file extension is `png` → `Frame.png`
* `[image name, %i]` for an image named `Frame.png` if the file extension is `png` → `Frame.png`
* `[image name, %n]` for an image named `Frame.png` if the file extension is `png` → `Frame`
* `[image name, %e]` for an image named `Frame.png` if the file extension is `jpg` → `Frame.jpg`
* `[image name, %i]` for an image named `Frame.png` if the file extension is `jpg` → `Frame`
* `[image name, %n]` for an image named `Frame.png` if the file extension is `jpg` → `Frame.jpg`

### \[image path\]

*Only available for: Batch Convert*

The "full path" of an image, from its topmost folder added as input to the image itself. This does not include folders above the folder added as input.

For example, if the folder named `Body` contains a subfolder named `Hands` which contains an image named `Left`, the image path will be `Body-Hands-Left`.

Options:
* *separator*: A string separating the path components.
  Defaults to `-`.
* *wrapper*: A string that wraps around each path component.
  The wrapper must contain `%c` denoting the path component.
  Defaults to `%c`.
* *file extension strip mode*: See the `\[image name\]` field.

Examples:
* `[image path]` → `Body-Hands-Left`
* `[image path, _]` → `Body_Hands_Left`
* `[image path, _, (%c)]` → `(Body)_(Hands)_(Left)`
* `[image path, _, (%c), %e]` → `Body-Hands-Left.png` (if the image name is `Left.png` and the file extension is `png`)

### \[layer name\]

*Only available for: Export Layers, Edit Layers*

The layer name.

Options:
* *file extension strip mode*:
	* `%e`: Never strip the extension.
	* `%i` (does not apply to Edit Layers): Strip the extension only if the layer has a file extension that does not match the entered file extension.
	* `%n` (does not apply to Edit Layers): Strip the extension only if the layer has a file extension that matches the entered file extension (the inverse of `%i`).

Examples:
* `[layer name]` for a layer named `Frame` → `Frame`
* `[layer name]` for a layer named `Frame.png` → `Frame`
* `[layer name, %e]` for a layer named `Frame.png` if the file extension is `png` → `Frame.png`
* `[layer name, %i]` for a layer named `Frame.png` if the file extension is `png` → `Frame.png`
* `[layer name, %n]` for a layer named `Frame.png` if the file extension is `png` → `Frame`
* `[layer name, %e]` for a layer named `Frame.png` if the file extension is `jpg` → `Frame.jpg`
* `[layer name, %i]` for a layer named `Frame.png` if the file extension is `jpg` → `Frame`
* `[layer name, %n]` for a layer named `Frame.png` if the file extension is `jpg` → `Frame.jpg`

### Full layer name

*Only available for: Export Layers, Edit Layers*

Equivalent to `[layer name, %e]`.

### \[layer path\]

The "full path" of a layer.
For example, if the image has a group layer named `Body` containing a group layer named `Hands` containing a layer named `Left`, the layer path will be `Body-Hands-Left`.

Options:
* *separator*: A string separating the path components.
  Defaults to `-`.
* *wrapper*: A string that wraps around each path component.
  The wrapper must contain `%c` denoting the path component.
  Defaults to `%c`.
* *file extension strip mode*: See the `\[layer name\]` field.

Examples:
* `[layer path]` → `Body-Hands-Left`
* `[layer path, _]` → `Body_Hands_Left`
* `[layer path, _, (%c)]` → `(Body)_(Hands)_(Left)`
* `[layer path, _, (%c), %e]` → `Body-Hands-Left.png` (if the layer name is `Left.png` and the file extension is `png`)

### \[output folder\]

The output folder selected in the plug-in dialog.

Options:
* *path component strip mode* (defaults to `%b`):
  * `%b<number>`: Keep only `<number>` path components from the end. `%b` is transformed to the last path component, i.e. the folder name.
  * `%f<number>`: Keep only `<number>` path components from the start.
  * any other value, such as `%`, will resolve to the full path.
* *separator*: A string separating the path components.
  Defaults to `-`.
* *wrapper*: A string that wraps around each path component.
  The wrapper must contain `%c` denoting the path component.
  Defaults to `%c`.

Examples for a folder with the path `C:\Users\username\Pictures`:
* `[output folder]` → `Pictures`
* `[output folder, %]` → `C-Users-username-Pictures`
* `[output folder, %b2]` → `username-Pictures`
* `[output folder, %b2, _]` → `username_Pictures`
* `[output folder, %b2, _, (%c)]` → `(username)_(Pictures)`
* `[output folder, %f2]` → `C-Users`

### \[replace\]

Replaces a part of the specified field with another string using a regular expression.
This essentially allows you to fine-tune any field.

Options:
* *field name*: Any recognized field described in this section, except "Number".
The field can be specified with options; if so, enclose the field in square brackets (`[` and `]`).
* *pattern*: Regular expression representing the part to be replaced.
Use the same syntax as defined in the [`re` module for Python](https://docs.python.org/3/library/re.html).
* *replacement*: Regular expression representing the replacement.
Use the same syntax as defined in the [`re` module for Python](https://docs.python.org/3/library/re.html).
* (optional) *count*: Number of replacements to perform if the pattern matches multiple parts.
If 0, perform replacements for all parts.
* (optional) *flags*: Flags further adjusting how the replacement should be performed.
Flags are specified in the [`re` module for Python](https://docs.python.org/3/library/re.html).
Use the name without the `re.` prefix.
For example, to ignore case, type `IGNORECASE` or `ignorecase`.
You can specify multiple flags separated by commas.

For the example below, suppose that an image is named `Animal copy #1`.
While the square brackets (`[` and `]`) enclosing the first three field options are optional, they are necessary in case you need to specify an empty string (`[]`), leading spaces or commas.

Examples:
* `[replace, [image name], [a], [b] ]` → `Animbl copy #1`
* `[replace, [image name], [a], [b], 1, ignorecase]` → `bnimal copy #1`
* `[replace, [image name], [ copy(?: #[[0-9]]+)*$], [] ]` → `Animal`

### \[tags\]

*Only available for: Export Layers, Edit Layers*

[Color tag](https://docs.gimp.org/en/gimp-layer-new.html) assigned to a layer.
For example, suppose that a layer has a green color tag assigned.
Then (by default) the tag will be formatted as `green`.

Options:
* *wrapper*: A string that wraps around each tag.
  The wrapper must contain `%t` denoting the tag.
* *color name, custom name, ...*: Color name in English followed by a custom name for the color. This allows you to map the color name to something else, e.g. `green` to `background`. You can specify multiple such pairs in case your image contains layers with different color tags.

Examples:
* `[tags]` → `green`
* `[tags, %t, green, background]` → `background`
* `[tags, (%t), green, background]` → `(background)`
* `[tags, %t, blue, foreground]` → *(empty string)*
* `[tags, %t, green, background, blue, foreground]` → `background`

### \[current date\]

The current date.

Options:
* *format*: Date format as per the [Python `strftime` function](http://strftime.org/).
  Defaults to `%Y-%m-%d` (year-month-day).

Examples:
* `[current date]` → `2019-01-28`
* `[current date, %m.%d.%Y_%H-%M]` → `28.01.2019_19-04`

### \[attributes\]

Attributes of the current image and the current Layer.

Options:
* *pattern*: A string formatting the attributes.
  Available attributes:
  * `%iw`: The image width.
  * `%ih`: The image height.
  * `%lw`: The layer width.
  * `%lh`: The layer height.
  * `%lx`: The layer *x*-offset.
  * `%ly`: The layer *y*-offset.
* *measure*: The measure in which the attribute values are displayed.
  Applies to `%lw`, `%lh`, `%lx` and `%ly` only.
  Available measures:
  * `%px` (default): Display absolute values in pixels.
  * `%pc`: Display percentages relative to the image.
    A number may be included after `%pc` to specify the number of digits to round to (2 by default).
    For example, `%pc1` displays percentages rounded to a single decimal digit.

Examples:
* `[attributes, %lw-%lh-%lx-%ly]` → `1000-270-0-40`
* `[attributes, %lw-%lh-%lx-%ly, %pc]` → `1.0-0.54-0.0-0.08`
* `[attributes, %lw-%lh-%lx-%ly, %pc1]` → `1.0-0.5-0.0-0.1`
* `[attributes, %iw-%ih]` → `1000-500`


## Inserting reserved characters in options

To insert a literal space or comma in a field option, enclose the option with square brackets.
To insert a literal square bracket (`[` or `]`), double the bracket and enclose the option with square brackets (e.g. `[[[]` to insert a literal `[`).

If the last option is enclosed in square brackets, leave a single space between the last and the second to last closing square bracket.

Examples:
* `[image path, [ ] ]` → `Body Hands Left`
* `[image path, [,], [[[%c]]] ]` → `[Body],[Hands],[Left]`
