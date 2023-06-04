import inspect
from collections.abc import Iterable
from functools import wraps
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from flask import Response, current_app, jsonify, request
from flask.typing import ResponseReturnValue, RouteCallable
from typing_extensions import get_args

try:
    from flask_restful import (  # type: ignore
        original_flask_make_response as make_response,
    )
except ImportError:
    from flask import make_response

from pydantic import BaseModel, ValidationError
from pydantic.tools import parse_obj_as

from .converters import convert_query_params
from .exceptions import (
    InvalidIterableOfModelsException,
    JsonBodyParsingError,
    ManyModelValidationError,
)
from .exceptions import ValidationError as FailedValidation

if TYPE_CHECKING:
    from pydantic.error_wrappers import ErrorDict


ModelResponseReturnValue = Union[ResponseReturnValue, BaseModel]
ModelRouteCallable = Union[
    Callable[..., ModelResponseReturnValue],
    Callable[..., Awaitable[ModelResponseReturnValue]],
]


def make_json_response(
    content: "Union[BaseModel, Iterable[BaseModel]]",
    status_code: int,
    by_alias: bool,
    exclude_none: bool = False,
) -> Response:
    """serializes model, creates JSON response with given status code"""
    if not isinstance(content, BaseModel):
        js = "["
        js += ", ".join(
            [
                model.json(exclude_none=exclude_none, by_alias=by_alias)
                for model in content
            ]
        )
        js += "]"
    else:
        js = content.json(exclude_none=exclude_none, by_alias=by_alias)
    response = make_response(js, status_code)
    response.mimetype = "application/json"
    return response


def unsupported_media_type_response(request_cont_type: str) -> Response:
    body = {
        "detail": f"Unsupported media type '{request_cont_type}' in request. "
        "'application/json' is required."
    }
    return make_response(jsonify(body), 415)


def is_iterable_of_models(content: Any) -> bool:
    try:
        return all(isinstance(obj, BaseModel) for obj in content)
    except TypeError:
        return False


def validate_many_models(model: Type[BaseModel], content: Any) -> List[BaseModel]:
    try:
        return [model(**fields) for fields in content]
    except TypeError:
        # iteration through `content` fails
        err: List["ErrorDict"] = [
            {
                "loc": ("root",),
                "msg": "is not an array of objects",
                "type": "type_error.array",
            }
        ]
        raise ManyModelValidationError(err)
    except ValidationError as ve:
        raise ManyModelValidationError(ve.errors())


def validate_path_params(
    func: ModelRouteCallable, kwargs: Dict[str, Any]
) -> Tuple[Dict[str, Any], List["ErrorDict"]]:
    errors: List["ErrorDict"] = []
    validated = {}
    for name, type_ in func.__annotations__.items():
        if name in {"query", "body", "form", "return"}:
            continue
        try:
            value = parse_obj_as(type_, kwargs.get(name))
            validated[name] = value
        except ValidationError as error:
            err = error.errors()[0]
            err["loc"] = (name,)
            errors.append(err)
    kwargs = {**kwargs, **validated}
    return kwargs, errors


def get_body_dict(**params: Dict[str, Any]) -> Any:
    data = request.get_json(**params)  # type: ignore
    if data is None and params.get("silent"):
        return {}
    return data


def _get_type_generic(hint: Any):
    """Extract type information from bound TypeVar or Type[TypeVar].

    Examples:

    ```
    MyGeneric = TypeVar("MyGeneric", bound=str)
    MyGenericType = Type[MyGeneric]

    _get_type_generic(str) -> str
    _get_type_generic(MyGeneric) -> str
    _get_type_generic(MyGenericType) -> str
    ```
    """
    # First check for direct TypeVar hint.
    if isinstance(hint, TypeVar):
        assert (
            getattr(hint, "__bound__", None) is not None
        ), "If using TypeVar, you need to specify bound model."
        return getattr(hint, "__bound__")

    # Check for Type[TypeVar] hint.
    args = get_args(hint)
    if len(args) > 0 and isinstance(args[0], TypeVar):
        assert (
            getattr(args[0], "__bound__", None) is not None
        ), "If using TypeVar, you need to specify bound model."
        return getattr(args[0], "__bound__")

    # Otherwise, use the type hint directly.
    return hint


def _ensure_model_kwarg(
    kwarg_name: str,
    from_validate: Optional[Type[BaseModel]],
    func: ModelRouteCallable,
) -> Tuple[Optional[Type[BaseModel]], bool]:
    """Get model information either from wrapped function or validate kwargs."""
    func_spec = inspect.getfullargspec(func)
    in_func_arg = kwarg_name in func_spec.args or kwarg_name in func_spec.kwonlyargs
    from_func = _get_type_generic(func_spec.annotations.get(kwarg_name))
    if from_func is None or not isinstance(from_func, type):
        return _get_type_generic(from_validate), in_func_arg

    # Ensure that the most "detailed" model is used.
    if from_validate is None:
        return from_func, in_func_arg
    if issubclass(from_func, from_validate):
        return from_func, in_func_arg
    return from_validate, in_func_arg


def validate(
    body: Optional[Type[BaseModel]] = None,
    query: Optional[Type[BaseModel]] = None,
    on_success_status: int = 200,
    exclude_none: bool = False,
    response_many: bool = False,
    request_body_many: bool = False,
    response_by_alias: bool = False,
    get_json_params: Optional[Dict[str, Any]] = None,
    form: Optional[Type[BaseModel]] = None,
):
    """
    Decorator for route methods which will validate query, body and form parameters
    as well as serialize the response (if it derives from pydantic's BaseModel
    class).

    Request parameters are accessible via flask's `request` variable:
        - request.query_params
        - request.body_params
        - request.form_params

    Or directly as `kwargs`, if you define them in the decorated function.

    `exclude_none` whether to remove None fields from response
    `response_many` whether content of response consists of many objects
        (e. g. List[BaseModel]). Resulting response will be an array of serialized
        models.
    `request_body_many` whether response body contains array of given model
        (request.body_params then contains list of models i. e. List[BaseModel])
    `response_by_alias` whether Pydantic's alias is used
    `get_json_params` - parameters to be passed to Request.get_json() function

    example::

        from flask import request
        from flask_pydantic import validate
        from pydantic import BaseModel

        class Query(BaseModel):
            query: str

        class Body(BaseModel):
            color: str

        class Form(BaseModel):
            name: str

        class MyModel(BaseModel):
            id: int
            color: str
            description: str

        ...

        @app.route("/")
        @validate(query=Query, body=Body, form=Form)
        def test_route():
            query = request.query_params.query
            color = request.body_params.query

            return MyModel(...)

        @app.route("/kwargs")
        @validate()
        def test_route_kwargs(query:Query, body:Body, form:Form):

            return MyModel(...)

    -> that will render JSON response with serialized MyModel instance
    """

    def decorate(func: ModelRouteCallable) -> RouteCallable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Dict[str, Any]) -> ResponseReturnValue:
            q, b, f, err = None, None, None, FailedValidation()
            func_kwargs, path_err = validate_path_params(func, kwargs)
            if len(path_err) > 0:
                err.path_params = path_err
            query_model, query_in_kwargs = _ensure_model_kwarg("query", query, func)
            if query_model is not None:
                query_params = convert_query_params(request.args, query_model)
                try:
                    q = query_model(**query_params)
                except ValidationError as ve:
                    err.query_params = ve.errors()
            body_model, body_in_kwargs = _ensure_model_kwarg("body", body, func)
            if body_model is not None:
                body_params = get_body_dict(**(get_json_params or {}))
                try:
                    if "__root__" in body_model.__fields__:
                        b = body_model(__root__=body_params).__root__  # type: ignore
                    elif request_body_many:
                        b = validate_many_models(body_model, body_params)
                    else:
                        b = body_model(**body_params)
                except (ValidationError, ManyModelValidationError) as error:
                    err.body_params = error.errors()
                except TypeError as error:
                    content_type = request.headers.get("Content-Type", "").lower()
                    media_type = content_type.split(";")[0]
                    if media_type != "application/json":
                        return unsupported_media_type_response(content_type)
                    else:
                        raise JsonBodyParsingError() from error
            form_model, form_in_kwargs = _ensure_model_kwarg("form", form, func)
            if form_model is not None:
                form_params = request.form
                try:
                    if "__root__" in form_model.__fields__:
                        f = form_model(__root__=form_params).__root__  # type: ignore
                    else:
                        f = form_model(**form_params)
                except TypeError as error:
                    content_type = request.headers.get("Content-Type", "").lower()
                    media_type = content_type.split(";")[0]
                    if media_type != "multipart/form-data":
                        return unsupported_media_type_response(content_type)
                    else:
                        raise JsonBodyParsingError() from error
                except ValidationError as ve:
                    err.form_params = ve.errors()
            request.query_params = q  # type: ignore
            request.body_params = b  # type: ignore
            request.form_params = f  # type: ignore
            if query_in_kwargs:
                func_kwargs["query"] = q
            if body_in_kwargs:
                func_kwargs["body"] = b
            if form_in_kwargs:
                func_kwargs["form"] = f

            if err.check():
                if current_app.config.get(
                    "FLASK_PYDANTIC_VALIDATION_ERROR_RAISE", False
                ):
                    raise err
                else:
                    status_code = current_app.config.get(
                        "FLASK_PYDANTIC_VALIDATION_ERROR_STATUS_CODE", 400
                    )
                    return make_response(
                        jsonify({"validation_error": err.to_dict()}), status_code
                    )
            res: ModelResponseReturnValue = current_app.ensure_sync(func)(
                *args, **func_kwargs
            )

            if response_many:
                if not is_iterable_of_models(res):
                    raise InvalidIterableOfModelsException(res)

                return make_json_response(
                    res,  # type: ignore  # Iterability and type is ensured above.
                    on_success_status,
                    by_alias=response_by_alias,
                    exclude_none=exclude_none,
                )

            if isinstance(res, BaseModel):
                return make_json_response(
                    res,
                    on_success_status,
                    exclude_none=exclude_none,
                    by_alias=response_by_alias,
                )

            if (
                isinstance(res, tuple)
                and len(res) in [2, 3]
                and isinstance(res[0], BaseModel)
            ):
                headers: Optional[
                    Union[Dict[str, Any], Tuple[Any, ...], List[Any]]
                ] = None
                status = on_success_status
                if isinstance(res[1], (dict, tuple, list)):
                    headers = res[1]
                elif isinstance(res[1], int):
                    status = res[1]

                # Following type ignores should be fixed once
                # https://github.com/python/mypy/issues/1178 is fixed.
                if len(res) == 3 and isinstance(
                    res[2], (dict, tuple, list)  # type: ignore[misc]
                ):
                    headers = res[2]  # type: ignore[misc]

                ret = make_json_response(
                    res[0],
                    status,
                    exclude_none=exclude_none,
                    by_alias=response_by_alias,
                )
                if headers is not None:
                    ret.headers.update(headers)
                return ret

            return res

        return wrapper

    return decorate
