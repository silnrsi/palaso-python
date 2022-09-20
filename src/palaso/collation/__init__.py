import warnings

__all__ = ['tailor', 'icu']

warnings.warn(
    """palaso.collation is deprecated. It will be replaced by https://github.com/silnrsi/collation
       in the near future. The sort_trainer script has already moved there.""",
    DeprecationWarning,
    stacklevel=2)
