"""A dialog handler for discord.py to make multipart dialog through Discord easy.

:copyright: (c) 2022 Tanner B. Corcoran
:license: MIT, see LICENSE for more details.
"""

__title__ = "dpy-dialog"
__author__ = "Tanner B. Corcoran"
__email__ = "tannerbcorcoran@gmail.com"
__license__ = "MIT License"
__copyright__ = "Copyright (c) 2022 Tanner B. Corcoran"
__version__ = "0.0.1"
__description__ = "A dialog handler for discord.py to make multipart dialog through Discord easy"
__url__ = "https://github.com/tanrbobanr/dpy-dialog"
__download_url__ = "https://pypi.org/project/dpy-dialog/"


__all__ = (
    "Dialog",
    "Config",
    "Formatter",
    "exceptions",
    "constants",
    "default_formatters"
)


from ._dialog import Dialog
from ._config import Config
from ._formatter import Formatter
from . import exceptions
from . import constants
from . import default_formatters
