from typing import List, Optional

import pytest
from flask import request
from pydantic import BaseModel
from flask_pydantic import validate


class ArrayModel(BaseModel):
    arr1: List[str]
    arr2: Optional[List[int]]


@pytest.fixture
def app_with_array_route(app):
    @app.route("/arr", methods=["GET"])
    @validate(query=ArrayModel, exclude_none=True)
    def pass_array():
        print(request.query_params)
        return ArrayModel(
            arr1=request.query_params.arr1, arr2=request.query_params.arr2
        )


@pytest.fixture
def app_with_camel_route(app):
    def to_camel(x: str) -> str:
        first, *rest = x.split("_")
        return "".join([first] + [x.capitalize() for x in rest])

    class RequestModel(BaseModel):
        x: int
        y: int

    class ResultModel(BaseModel):
        result_of_addition: int
        result_of_multiplication: int

        class Config:
            alias_generator = to_camel
            allow_population_by_field_name = True

    @app.route("/compute", methods=["GET"])
    @validate(response_by_alias=True)
    def compute(query: RequestModel):
        return ResultModel(
            result_of_addition=query.x + query.y,
            result_of_multiplication=query.x * query.y,
        )


test_cases = [
    pytest.param(
        "?limit=limit",
        {"search_term": "text"},
        400,
        {
            "validation_error": {
                "query_params": [
                    {
                        "loc": ["limit"],
                        "msg": "value is not a valid integer",
                        "type": "type_error.integer",
                    }
                ]
            }
        },
        id="invalid limit",
    ),
    pytest.param(
        "?limit=2",
        {},
        400,
        {
            "validation_error": {
                "body_params": [
                    {
                        "loc": ["search_term"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    }
                ]
            }
        },
        id="missing required body parameter",
    ),
    pytest.param(
        "?limit=1&min_views=2",
        {"search_term": "text"},
        200,
        {"count": 2, "results": [{"title": "2", "text": "another text", "views": 2}]},
        id="valid parameters",
    ),
    pytest.param(
        "",
        {"search_term": "text"},
        200,
        {
            "count": 3,
            "results": [
                {"title": "title 1", "text": "random text", "views": 1},
                {"title": "2", "text": "another text", "views": 2},
            ],
        },
        id="valid params, no query",
    ),
]


class TestSimple:
    @pytest.mark.parametrize("query,body,expected_status,expected_response", test_cases)
    def test_post(self, client, query, body, expected_status, expected_response):
        response = client.post(f"/search{query}", json=body)
        assert response.json == expected_response
        assert response.status_code == expected_status

    @pytest.mark.parametrize("query,body,expected_status,expected_response", test_cases)
    def test_post_kwargs(self, client, query, body, expected_status, expected_response):
        response = client.post(f"/search/kwargs{query}", json=body)
        assert response.json == expected_response
        assert response.status_code == expected_status

    def test_error_status_code(self, app, mocker, client):
        mocker.patch.dict(
            app.config, {"FLASK_PYDANTIC_VALIDATION_ERROR_STATUS_CODE": 422}
        )
        response = client.post("/search?limit=2", json={})
        assert response.status_code == 422


@pytest.mark.usefixtures("app_with_array_route")
class TestArrayQueryParam:
    def test_no_param_raises(self, client):
        response = client.get("/arr")
        assert response.json == {
            "validation_error": {
                "query_params": [
                    {
                        "loc": ["arr1"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    }
                ]
            }
        }

    def test_correctly_returns_first_arr(self, client):
        response = client.get("/arr?arr1=first&arr1=second")
        assert response.json == {"arr1": ["first", "second"]}

    def test_correctly_returns_first_arr_one_element(self, client):
        response = client.get("/arr?arr1=first")
        assert response.json == {"arr1": ["first"]}

    def test_correctly_returns_both_arrays(self, client):
        response = client.get("/arr?arr1=first&arr1=second&arr2=1&arr2=10")
        assert response.json == {"arr1": ["first", "second"], "arr2": [1, 10]}


aliases_test_cases = [
    pytest.param(1, 2, {"resultOfMultiplication": 2, "resultOfAddition": 3}),
    pytest.param(10, 20, {"resultOfMultiplication": 200, "resultOfAddition": 30}),
    pytest.param(999, 0, {"resultOfMultiplication": 0, "resultOfAddition": 999}),
]


@pytest.mark.usefixtures("app_with_camel_route")
@pytest.mark.parametrize("x,y,expected_result", aliases_test_cases)
def test_aliases(x, y, expected_result, client):
    response = client.get(f"/compute?x={x}&y={y}")
    assert response.json == expected_result
