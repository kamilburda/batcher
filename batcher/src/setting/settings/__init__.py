"""Setting classes."""

# Despite being unused, `presenters_gtk` must be imported so that the GUI
# classes defined in each `setting.Setting` class are properly registered and
# ``SETTING_GUI_TYPES`` is filled.
# noinspection PyUnresolvedReferences
from .. import presenters_gtk

from ._array import *
from ._base import *
from ._bool import *
from ._bytes import *
from ._choice import *
from ._color import *
from ._container import *
from ._display import *
from ._enum import *
from ._export_options import *
from ._file import *
from ._functions import *
from ._generic import *
from ._gimp_objects import *
from ._numeric import *
from ._parasite import *
from ._resource import *
from ._string import *
from ._unit import *
