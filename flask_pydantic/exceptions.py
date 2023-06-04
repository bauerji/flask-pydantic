from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, List, Optional

if TYPE_CHECKING:
    from pydantic.error_wrappers import ErrorDict


class BaseFlaskPydanticException(Exception):
    """Base exc class for all exception from this library"""

    pass


class InvalidIterableOfModelsException(BaseFlaskPydanticException):
    """This exception is raised if there is a failure during serialization of
    response object with `response_many=True`"""

    pass


class JsonBodyParsingError(BaseFlaskPydanticException):
    """Exception for error occurring during parsing of request body"""

    pass


class ManyModelValidationError(BaseFlaskPydanticException):
    """This exception is raised if there is a failure during validation of many
    models in an iterable"""

    def __init__(self, errors: List["ErrorDict"], *args: Any):
        self._errors = errors
        super().__init__(*args)

    def errors(self):
        return self._errors


@dataclass
class ValidationError(BaseFlaskPydanticException):
    """This exception is raised if there is a failure during validation if the
    user has configured an exception to be raised instead of a response"""

    body_params: Optional[List["ErrorDict"]] = None
    form_params: Optional[List["ErrorDict"]] = None
    path_params: Optional[List["ErrorDict"]] = None
    query_params: Optional[List["ErrorDict"]] = None

    def check(self) -> bool:
        """Check if any param resulted in error."""
        return any(value is not None for _, value in asdict(self).items())

    def to_dict(self):
        return {key: value for key, value in asdict(self).items() if value is not None}
