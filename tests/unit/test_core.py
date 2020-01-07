from typing import NamedTuple, Optional, Type

import pytest
from flask import jsonify
from flask_pydantic import validate
from pydantic import BaseModel


class ValidateParams(NamedTuple):
    body_model: Optional[Type[BaseModel]] = None
    query_model: Optional[Type[BaseModel]] = None
    response_model: Type[BaseModel] = None
    on_success_status: int = 200
    request_query: dict = {}
    request_body: dict = {}
    expected_response_body: Optional[dict] = None
    expected_status_code: int = 200


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
