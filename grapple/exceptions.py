class IllegalDeprecation(Exception):
    """
    A Collection or Field was marked as required, but also received a `deprecation_reason'.

    This is invalid - a deprecated entity must be nullable.
    """

    pass
