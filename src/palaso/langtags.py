import warnings
from sldr.langtags_full import * # noqa

warnings.warn(
    "palaso.langtags is deprecated. Please use sldr.langtags_full instead.",
    DeprecationWarning,
    stacklevel=2)
