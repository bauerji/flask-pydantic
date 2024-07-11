from ..util import assert_matches
import re
from typing import List, Optional

import pytest
from flask import jsonify, request
from flask_pydantic import validate, ValidationError
from pydantic import BaseModel, RootModel, ConfigDict


class ArrayModel(BaseModel):
    arr1: List[str]
    arr2: Optional[List[int]] = None


@pytest.fixture
def app_with_array_route(app):
    @app.route("/arr", methods=["GET"])
    @validate(query=ArrayModel, exclude_none=True)
    def pass_array():
        return ArrayModel(
            arr1=request.query_params.arr1, arr2=request.query_params.arr2
        )


@pytest.fixture
def app_with_optional_body(app):
    class Body(BaseModel):
        param: str

    @app.route("/no_params", methods=["POST"])
    @validate()
    def no_params(body: Body):
        return body

    @app.route("/silent", methods=["POST"])
    @validate(get_json_params={"silent": True})
    def silent(body: Body):
        return body


@pytest.fixture
def app_raise_on_validation_error(app):
    app.config["FLASK_PYDANTIC_VALIDATION_ERROR_RAISE"] = True

    def validation_error(error: ValidationError):
        return (
            jsonify(
                {
                    "title": "validation error",
                    "body": error.body_params,
                }
            ),
            422,
        )

    app.register_error_handler(ValidationError, validation_error)

    class Body(BaseModel):
        param: str

    @app.route("/silent", methods=["POST"])
    @validate(get_json_params={"silent": True})
    def silent(body: Body):
        return body


@pytest.fixture
def app_with_int_path_param_route(app):
    class IdObj(BaseModel):
        id: int

    @app.route("/path_param/<obj_id>/", methods=["GET"])
    @validate()
    def int_path_param(obj_id: int):
        return IdObj(id=obj_id)


@pytest.fixture
def app_with_untyped_path_param_route(app):
    class IdObj(BaseModel):
        id: str

    @app.route("/path_param/<obj_id>/", methods=["GET"])
    @validate()
    def int_path_param(obj_id):
        return IdObj(id=obj_id)


@pytest.fixture
def app_with_non_pydantic_argument(app):
    class IdObj(BaseModel):
        id: str

    @app.route("/path_param/<obj_id>/", methods=["GET"])
    @validate()
    def int_path_param(obj_id: str, non_pydantic: ValidationError = None):
        return IdObj(id=obj_id)


@pytest.fixture
def app_with_custom_root_type(app):
    class Person(BaseModel):
        name: str
        age: Optional[int] = None

    class PersonBulk(RootModel):
        root: List[Person]

        def __len__(self):
            return len(self.root)

    @app.route("/root_type", methods=["POST"])
    @validate()
    def root_type(body: PersonBulk):
        return {"number": len(body)}


@pytest.fixture
def app_with_custom_headers(app):
    @app.route("/custom_headers", methods=["GET"])
    @validate()
    def custom_headers():
        return {"test": 1}, {"CUSTOM_HEADER": "UNIQUE"}


@pytest.fixture
def app_with_custom_headers_status(app):
    @app.route("/custom_headers_status", methods=["GET"])
    @validate()
    def custom_headers():
        return {"test": 1}, 201, {"CUSTOM_HEADER": "UNIQUE"}


@pytest.fixture
def app_with_camel_route(app):
    def to_camel(x: str) -> str:
        first, *rest = x.split("_")
        return "".join([first] + [x.capitalize() for x in rest])

    class RequestModel(BaseModel):
        x: int
        y: int

    class ResultModel(BaseModel):
        model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

        result_of_addition: int
        result_of_multiplication: int

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
                        "input": "limit",
                        "loc": ["limit"],
                        "msg": "Input should be a valid integer, unable to parse string as an integer",
                        "type": "int_parsing",
                        "url": re.compile(
                            r"https://errors\.pydantic\.dev/.*/v/int_parsing"
                        ),
                    }
                ],
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
                        "input": {},
                        "loc": ["search_term"],
                        "msg": "Field required",
                        "type": "missing",
                        "url": re.compile(
                            r"https://errors\.pydantic\.dev/.*/v/missing"
                        ),
                    }
                ],
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

form_test_cases = [
    pytest.param(
        "?limit=2",
        {},
        400,
        {
            "validation_error": {
                "form_params": [
                    {
                        "input": {},
                        "loc": ["search_term"],
                        "msg": "Field required",
                        "type": "missing",
                        "url": re.compile(
                            r"https://errors\.pydantic\.dev/.*/v/missing"
                        ),
                    }
                ]
            }
        },
        id="missing required form parameter",
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
        assert_matches(expected_response, response.json)
        assert response.status_code == expected_status

    @pytest.mark.parametrize("query,body,expected_status,expected_response", test_cases)
    def test_post_kwargs(self, client, query, body, expected_status, expected_response):
        response = client.post(f"/search/kwargs{query}", json=body)
        assert_matches(expected_response, response.json)
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        "query,form,expected_status,expected_response", form_test_cases
    )
    def test_post_kwargs_form(
        self, client, query, form, expected_status, expected_response
    ):
        response = client.post(
            f"/search/form/kwargs{query}",
            data=form,
        )
        assert_matches(expected_response, response.json)
        assert response.status_code == expected_status

    def test_error_status_code(self, app, mocker, client):
        mocker.patch.dict(
            app.config, {"FLASK_PYDANTIC_VALIDATION_ERROR_STATUS_CODE": 422}
        )
        response = client.post("/search?limit=2", json={})
        assert response.status_code == 422


@pytest.mark.usefixtures("app_with_custom_root_type")
def test_custom_root_types(client):
    response = client.post(
        "/root_type",
        json=[{"name": "Joshua Bardwell", "age": 46}, {"name": "Andrew Cambden"}],
    )
    assert response.json == {"number": 2}


@pytest.mark.usefixtures("app_with_custom_headers")
def test_custom_headers(client):
    response = client.get("/custom_headers")
    assert response.json == {"test": 1}
    assert response.status_code == 200
    assert response.headers.get("CUSTOM_HEADER") == "UNIQUE"


@pytest.mark.usefixtures("app_with_custom_headers_status")
def test_custom_headers(client):
    response = client.get("/custom_headers_status")
    assert response.json == {"test": 1}
    assert response.status_code == 201
    assert response.headers.get("CUSTOM_HEADER") == "UNIQUE"


@pytest.mark.usefixtures("app_with_array_route")
class TestArrayQueryParam:
    def test_no_param_raises(self, client):
        response = client.get("/arr")
        assert_matches(
            {
                "validation_error": {
                    "query_params": [
                        {
                            "input": {},
                            "loc": ["arr1"],
                            "msg": "Field required",
                            "type": "missing",
                            "url": re.compile(
                                r"https://errors\.pydantic\.dev/.*/v/missing"
                            ),
                        }
                    ]
                }
            },
            response.json,
        )

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
    assert_matches(expected_result, response.json)


@pytest.mark.usefixtures("app_with_int_path_param_route")
class TestPathIntParameter:
    def test_correct_param_passes(self, client):
        id_ = 12
        expected_response = {"id": id_}
        response = client.get(f"/path_param/{id_}/")
        assert_matches(expected_response, response.json)

    def test_string_parameter(self, client):
        expected_response = {
            "validation_error": {
                "path_params": [
                    {
                        "input": "not_an_int",
                        "loc": ["obj_id"],
                        "msg": "Input should be a valid integer, unable to parse string as an integer",
                        "type": "int_parsing",
                        "url": re.compile(
                            r"https://errors\.pydantic\.dev/.*/v/int_parsing"
                        ),
                    }
                ]
            }
        }
        response = client.get("/path_param/not_an_int/")

        assert_matches(expected_response, response.json)
        assert response.status_code == 400


@pytest.mark.usefixtures("app_with_untyped_path_param_route")
class TestPathUnannotatedParameter:
    def test_int_str_param_passes(self, client):
        id_ = 12
        expected_response = {"id": str(id_)}
        response = client.get(f"/path_param/{id_}/")

        assert_matches(expected_response, response.json)

    def test_str_param_passes(self, client):
        id_ = "twelve"
        expected_response = {"id": id_}
        response = client.get(f"/path_param/{id_}/")

        assert_matches(expected_response, response.json)


@pytest.mark.usefixtures("app_with_non_pydantic_argument")
class TestFunctionArgument:
    def test_int_str_param_passes(self, client):
        id_ = 12
        expected_response = {"id": str(id_)}
        response = client.get(f"/path_param/{id_}/")

        assert response.json == expected_response

    def test_str_param_passes(self, client):
        id_ = "twelve"
        expected_response = {"id": id_}
        response = client.get(f"/path_param/{id_}/")

        assert response.json == expected_response


@pytest.mark.usefixtures("app_with_optional_body")
class TestGetJsonParams:
    def test_empty_body_fails(self, client):
        response = client.post(
            "/no_params", headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 400
        assert (
            "failed to decode json object: expecting value: line 1 column 1 (char 0)"
            in response.text.lower()
        )

    def test_silent(self, client):
        response = client.post("/silent", headers={"Content-Type": "application/json"})

        assert_matches(
            {
                "validation_error": {
                    "body_params": [
                        {
                            "input": {},
                            "loc": ["param"],
                            "msg": "Field required",
                            "type": "missing",
                            "url": re.compile(
                                r"https://errors\.pydantic\.dev/.*/v/missing"
                            ),
                        }
                    ]
                }
            },
            response.json,
        )
        assert response.status_code == 400


@pytest.mark.usefixtures("app_raise_on_validation_error")
class TestCustomResponse:
    def test_silent(self, client):
        response = client.post("/silent", headers={"Content-Type": "application/json"})

        assert response.json["title"] == "validation error"
        assert_matches(
            [
                {
                    "input": {},
                    "loc": ["param"],
                    "msg": "Field required",
                    "type": "missing",
                    "url": re.compile(r"https://errors\.pydantic\.dev/.*/v/missing"),
                }
            ],
            response.json["body"],
        )
        assert response.status_code == 422
