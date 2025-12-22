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

    def __init__(self, errors: list[dict], *args):
        self._errors = errors
        super().__init__(*args)

    def errors(self):
        return self._errors


class ValidationError(BaseFlaskPydanticException):
    """This exception is raised if there is a failure during validation if the
    user has configured an exception to be raised instead of a response"""

    def __init__(
        self,
        body_params: list[dict] | None = None,
        form_params: list[dict] | None = None,
        path_params: list[dict] | None = None,
        query_params: list[dict] | None = None,
    ):
        super().__init__()
        self.body_params = body_params
        self.form_params = form_params
        self.path_params = path_params
        self.query_params = query_params
