from functools import wraps
from typing import Optional, Callable, TypeVar, Any

from flask import request, jsonify, make_response, Response
from pydantic import BaseModel, ValidationError

try:
    from flask_restful import original_flask_make_response as make_response
except ImportError:
    pass


InputParams = TypeVar("InputParams")


def make_json_response(model: BaseModel, status_code: int) -> Response:
    """serializes model, creates JSON response with given status code"""
    response = make_response(model.json(), status_code)
    response.mimetype = "application/json"
    return response


def validate(
    body: Optional[BaseModel] = None,
    query: Optional[BaseModel] = None,
    on_success_status: int = 200,
):
    """
    Decorator for route methods which will validate query and body parameters as well as
    serialize the response (if it derives from pydantic's BaseModel class).

    example:

    from flask import request
    from flask_pydantic import validate
    from pydantic import BaseModel

    class Query(BaseModel):
        query: str

    class Body(BaseModel):
        color: str

    class MyModel(BaseModel):
        id: int
        color: str
        description: str

    ...

    @app.route("/")
    @validate(query=Query, body=Body)
    def test_route():
        query = request.query_params.query
        color = request.body_params.query

        return MyModel(...)

    -> that will render JSON response with serialized MyModel instance
    """

    def decorate(func: Callable[[InputParams], Any]) -> Callable[[InputParams], Any]:
        @wraps(func)
        def wrapper(*args, **kwargs):
            query_params = request.args
            body_params = request.get_json()
            q, b, err = {}, {}, {}
            if query:
                try:
                    q = query(**query_params)
                except ValidationError as ve:
                    err["query_params"] = ve.errors()
            if body:
                try:
                    b = body(**body_params)
                except ValidationError as ve:
                    err["body_params"] = ve.errors()
            if err:
                return make_response(jsonify({"validation_error": err}), 400)
            request.query_params = q
            request.body_params = b
            res = func(*args, **kwargs)

            if isinstance(res, BaseModel):
                return make_json_response(res, on_success_status)

            if (
                isinstance(res, tuple)
                and len(res) == 2
                and isinstance(res[0], BaseModel)
            ):
                return make_json_response(res[0], res[1])

            return res

        return wrapper

    return decorate
