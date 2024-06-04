class PathDoesNotExistError(Exception):
    """Исключение, возникающее, когда путь не существует."""

class InvalidButtonTypeException(Exception):
    """Exception raised for errors in the input button type."""

class TypeMismatchException(Exception):
    """Exception raised when there is a type mismatch in the button construction."""


class InfinityCycleError(Exception):
    ...


class NoBroadcastDataError(Exception):
    pass
