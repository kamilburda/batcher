It is also possible to run Batcher without the interactive dialog, e.g. for automation purposes.

The `plug-in-batch-convert` procedure allows running Batch Convert non-interactively, using the supplied UTF-8-encoded file (the `inputs` parameter) containing files and folders on each line, plus other export parameters such as the output folder or file extension. If `run-mode` is `Gimp.RunMode.WITH_LAST_VALS`, all these parameters (including `inputs`) will be ignored and instead the settings last used interactively (in the main dialog) will be considered.

The `plug-in-batch-export-layers` procedure exports layers with the specified or the last used settings, depending on the value of the `run-mode` parameter.
Likewise, `plug-in-batch-edit-layers` runs batch editing layers with the specified/last used settings.

You can also run `plug-in-batch-convert`, `plug-in-batch-export-layers` or `plug-in-batch-edit-layers` with [settings imported from a file](../Usage.md#managing-settings) by specifying the `settings-file` parameter. In that case, the `run-mode` must be `Gimp.RunMode.NONINTERACTIVE` and all other procedure arguments will be ignored (since these arguments will be assigned values from the settings file). The exception is the `inputs` parameter for `plug-in-batch-convert`, which will always be considered and the saved input images in the settings file will be ignored.

The `plug-in-batch-export-layers-quick` and `plug-in-batch-edit-layers-quick` procedures perform layer export/editing with always the last used settings.
The `plug-in-batch-export-selected-layers` and `plug-in-batch-edit-selecetged-layers` procedures perform export/editing of selected layers with always the last used settings.

Example using `plug-in-batch-convert` in Python (e.g. the Python console in GIMP):
```
procedure = Gimp.get_pdb().lookup_procedure('plug-in-batch-convert')
config = procedure.create_config()
config.set_property('inputs', Gio.file_new_for_path('/home/username/Pictures/list_of_images.txt'))
config.set_property('file-extension', 'png')
config.set_property('output-directory', Gio.file_new_for_path('/home/username/Pictures/Output'))

result = procedure.run(config)
success = result.index(0)
```

Example using `plug-in-batch-convert` by running GIMP via command line (Unix shell) using a settings file:
```shell
gimp -nidfs --quit --batch-interpreter python-fu-eval -b "
procedure = Gimp.get_pdb().lookup_procedure('plug-in-batch-convert')
config = procedure.create_config()
config.set_property('run-mode', Gimp.RunMode.NONINTERACTIVE)
config.set_property('inputs', Gio.file_new_for_path('/home/username/Pictures/list_of_images.txt'))
config.set_property('file-extension', 'png')
config.set_property('output-directory', Gio.file_new_for_path('/home/username/Pictures/Output'))
config.set_property('settings-file', Gio.file_new_for_path('/home/username/Pictures/settings.json'))
procedure.run(config)
"
```

On Windows Powershell, you would use a similar syntax:
```powershell
gimp -nidfs --quit --batch-interpreter python-fu-eval -b @"
<insert Python code here>
"@
```
