from typing import NamedTuple, Optional, Type, Union, List

import pytest
from flask import jsonify
from pydantic import BaseModel

from flask_pydantic import validate
from flask_pydantic.exceptions import (
    InvalidIterableOfModelsException,
    JsonBodyParsingError,
)
from flask_pydantic.core import is_iterable_of_models


class ValidateParams(NamedTuple):
    body_model: Optional[Type[BaseModel]] = None
    query_model: Optional[Type[BaseModel]] = None
    response_model: Type[BaseModel] = None
    on_success_status: int = 200
    request_query: dict = {}
    request_body: Union[dict, List[dict]] = {}
    expected_response_body: Optional[dict] = None
    expected_status_code: int = 200
    exclude_none: bool = False
    response_many: bool = False
    request_body_many: bool = False


class ResponseModel(BaseModel):
    q1: int
    q2: str
    b1: float
    b2: Optional[str]


class QueryModel(BaseModel):
    q1: int
    q2: str = "default"


class RequestBodyModel(BaseModel):
    b1: float
    b2: Optional[str] = None


validate_test_cases = [
    pytest.param(
        ValidateParams(
            request_body={"b1": 1.4},
            request_query={"q1": 1},
            expected_response_body={"q1": 1, "q2": "default", "b1": 1.4, "b2": None},
            response_model=ResponseModel,
            query_model=QueryModel,
            body_model=RequestBodyModel,
        ),
        id="simple valid example with default values",
    ),
    pytest.param(
        ValidateParams(
            request_body={"b1": 1.4},
            request_query={"q1": 1},
            expected_response_body={"q1": 1, "q2": "default", "b1": 1.4},
            response_model=ResponseModel,
            query_model=QueryModel,
            body_model=RequestBodyModel,
            exclude_none=True,
        ),
        id="simple valid example with default values, exclude none",
    ),
    pytest.param(
        ValidateParams(
            query_model=QueryModel,
            expected_response_body={
                "validation_error": {
                    "query_params": [
                        {
                            "loc": ["q1"],
                            "msg": "field required",
                            "type": "value_error.missing",
                        }
                    ]
                }
            },
            expected_status_code=400,
        ),
        id="invalid query param",
    ),
    pytest.param(
        ValidateParams(
            body_model=RequestBodyModel,
            expected_response_body={
                "validation_error": {
                    "body_params": [
                        {
                            "loc": ["root"],
                            "msg": "is not an array of objects",
                            "type": "type_error.array",
                        }
                    ]
                }
            },
            request_body={"b1": 3.14, "b2": "str"},
            expected_status_code=400,
            request_body_many=True,
        ),
        id="`request_body_many=True` but in request body is a single object",
    ),
    pytest.param(
        ValidateParams(
            expected_response_body={
                "validation_error": {
                    "body_params": [
                        {
                            "loc": ["b1"],
                            "msg": "field required",
                            "type": "value_error.missing",
                        }
                    ]
                }
            },
            body_model=RequestBodyModel,
            expected_status_code=400,
        ),
        id="invalid body param",
    ),
    pytest.param(
        ValidateParams(
            expected_response_body={
                "validation_error": {
                    "body_params": [
                        {
                            "loc": ["b1"],
                            "msg": "field required",
                            "type": "value_error.missing",
                        }
                    ]
                }
            },
            body_model=RequestBodyModel,
            expected_status_code=400,
            request_body=[{}],
            request_body_many=True,
        ),
        id="invalid body param in many-object request body",
    ),
]


class TestValidate:
    @pytest.mark.parametrize("parameters", validate_test_cases)
    def test_validate(self, mocker, request_ctx, parameters: ValidateParams):
        mock_request = mocker.patch.object(request_ctx, "request")
        mock_request.args = parameters.request_query
        mock_request.get_json = lambda: parameters.request_body

        def f():
            return parameters.response_model(
                **mock_request.body_params.dict(), **mock_request.query_params.dict()
            )

        response = validate(
            query=parameters.query_model,
            body=parameters.body_model,
            on_success_status=parameters.on_success_status,
            exclude_none=parameters.exclude_none,
            response_many=parameters.response_many,
            request_body_many=parameters.request_body_many,
        )(f)()

        assert response.status_code == parameters.expected_status_code
        assert response.json == parameters.expected_response_body
        if 200 <= response.status_code < 300:
            assert (
                mock_request.body_params.dict(exclude_none=True, exclude_defaults=True)
                == parameters.request_body
            )
            assert (
                mock_request.query_params.dict(exclude_none=True, exclude_defaults=True)
                == parameters.request_query
            )

    @pytest.mark.usefixtures("request_ctx")
    def test_response_with_status(self):
        expected_status_code = 201
        expected_response_body = dict(q1=1, q2="2", b1=3.14, b2="b2")

        def f():
            return ResponseModel(q1=1, q2="2", b1=3.14, b2="b2"), expected_status_code

        response = validate()(f)()
        assert response.status_code == expected_status_code
        assert response.json == expected_response_body

    @pytest.mark.usefixtures("request_ctx")
    def test_response_already_response(self):
        expected_response_body = {"a": 1, "b": 2}

        def f():
            return jsonify(expected_response_body)

        response = validate()(f)()
        assert response.json == expected_response_body

    @pytest.mark.usefixtures("request_ctx")
    def test_response_many_response_objs(self):
        response_content = [
            ResponseModel(q1=1, q2="2", b1=3.14, b2="b2"),
            ResponseModel(q1=2, q2="3", b1=3.14),
            ResponseModel(q1=3, q2="4", b1=6.9, b2="b4"),
        ]
        expected_response_body = [
            {"q1": 1, "q2": "2", "b1": 3.14, "b2": "b2"},
            {"q1": 2, "q2": "3", "b1": 3.14},
            {"q1": 3, "q2": "4", "b1": 6.9, "b2": "b4"},
        ]

        def f():
            return response_content

        response = validate(exclude_none=True, response_many=True)(f)()
        assert response.json == expected_response_body

    @pytest.mark.usefixtures("request_ctx")
    def test_invalid_many_raises(self):
        def f():
            return ResponseModel(q1=1, q2="2", b1=3.14, b2="b2")

        with pytest.raises(InvalidIterableOfModelsException):
            validate(response_many=True)(f)()

    def test_valid_array_object_request_body(self, mocker, request_ctx):
        mock_request = mocker.patch.object(request_ctx, "request")
        mock_request.args = {"q1": 1}
        mock_request.get_json = lambda: [
            {"b1": 1.0, "b2": "str1"},
            {"b1": 2.0, "b2": "str2"},
        ]
        expected_response_body = [
            {"q1": 1, "q2": "default", "b1": 1.0, "b2": "str1"},
            {"q1": 1, "q2": "default", "b1": 2.0, "b2": "str2"},
        ]

        def f():
            query_params = mock_request.query_params
            body_params = mock_request.body_params
            return [
                ResponseModel(
                    q1=query_params.q1, q2=query_params.q2, b1=obj.b1, b2=obj.b2
                )
                for obj in body_params
            ]

        response = validate(
            query=QueryModel,
            body=RequestBodyModel,
            request_body_many=True,
            response_many=True,
        )(f)()

        assert response.status_code == 200
        assert response.json == expected_response_body

    def test_unsupported_media_type(self, request_ctx, mocker):
        mock_request = mocker.patch.object(request_ctx, "request")
        content_type = "text/plain"
        mock_request.headers = {"Content-Type": content_type}
        mock_request.get_json = lambda: None
        body_model = RequestBodyModel
        response = validate(body_model)(lambda x: x)()
        assert response.status_code == 415
        assert response.json == {
            "detail": f"Unsupported media type '{content_type}' in request. "
            "'application/json' is required."
        }

    def test_damaged_request_body(self, request_ctx, mocker):
        mock_request = mocker.patch.object(request_ctx, "request")
        content_type = "application/json"
        mock_request.headers = {"Content-Type": content_type}
        mock_request.get_json = lambda: None
        body_model = RequestBodyModel
        with pytest.raises(JsonBodyParsingError):
            validate(body_model)(lambda x: x)()


class TestIsIterableOfModels:
    def test_simple_true_case(self):
        models = [
            QueryModel(q1=1, q2="w"),
            QueryModel(q1=2, q2="wsdf"),
            RequestBodyModel(b1=3.1),
            RequestBodyModel(b1=0.1),
        ]
        assert is_iterable_of_models(models)

    def test_false_for_non_iterable(self):
        assert not is_iterable_of_models(1)

    def test_false_for_single_model(self):
        assert not is_iterable_of_models(RequestBodyModel(b1=12))
