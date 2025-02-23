"""Names that uniquely identify a group of related plug-in procedures.

For example, `EXPORT_LAYERS_GROUP` represents the
``'plug-in-batch-export-layers'`` and ``'plug-in-batch-export-layers-quick'``
procedures.

These names can be used, for example, for the following purposes:
* saving separate settings for each plug-in procedure,
* filtering actions applicable only to specific procedures,
* filtering name pattern fields applicable only to specific procedures.
"""

PROCEDURE_GROUPS = (
  CONVERT_GROUP,
  EXPORT_IMAGES_GROUP,
  EXPORT_LAYERS_GROUP,
  EDIT_LAYERS_GROUP,
) = (
  'plug-in-batch-convert',
  'plug-in-batch-export-images',
  'plug-in-batch-export-layers',
  'plug-in-batch-edit-layers',
)
