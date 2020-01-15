# Flask-Pydantic
[![Actions Status](https://github.com/bauerji/flask_pydantic/workflows/Python%20package/badge.svg?branch=master)](https://github.com/bauerji/flask_pydantic/actions)
[![PyPI](https://img.shields.io/pypi/v/Flask-Pydantic?color=g)](https://pypi.org/project/Flask-Pydantic/)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/bauerji/flask_pydantic.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/bauerji/flask_pydantic/context:python)
[![License](https://img.shields.io/badge/license-MIT-purple)](https://github.com/bauerji/flask_pydantic/blob/master/LICENSE)
[![Code style](https://img.shields.io/badge/code%20style-black-black)](https://github.com/psf/black)

Flask extension for integration of the awesome [pydantic package](https://github.com/samuelcolvin/pydantic) with [Flask](https://palletsprojects.com/p/flask/).

## Installation
``python3 -m pip install Flask-Pydantic``

## Basics
`validate` decorator validates query and body request parameters and makes them accessible via flask's `request` variable

| **parameter type** | **`request` attribute name** |
|:--------------:|:------------------------:|
| query          | `query_params`           |
| body           | `body_params`            |

- Success response status code can be modified via `on_success_status` parameter of `validate` decorator.
- `response_many` parameter set to `True` enables serialization of multiple models (route function should therefore return iterable of models).
- `request_body_many` parameter set to `False` analogically enables serialization of multiple models inside of the root level of request body. If the request body doesn't contain an array of objects `400` response is returned,
- If validation fails, `400` response is returned with failure explanation.

For more details see in-code docstring or example app.

## Usage
### Basic example
Simply use `validate` decorator on route function. 

:exclamation: Be aware that `@app.route` decorator must precede `@validate` (i. e. `@validate` must be closer to the function declaration).
```python
from typing import Optional

from flask import Flask, request
from flask_pydantic import validate
from pydantic import BaseModel

app = Flask("flask_pydantic_app")


class QueryModel(BaseModel):
    age: int


class BodyModel(BaseModel):
    name: str
    nickname: Optional[str]


class ResponseModel(BaseModel):
    id: int
    age: int
    name: str
    nickname: Optional[str]


@app.route("/", methods=["POST"])
@validate(body=BodyModel, query=QueryModel)
def post():
    # save model to DB
    id_ = ...

    return ResponseModel(
        id=id_,
        age=request.query_params.age,
        name=request.body_params.name,
        nickname=request.body_params.nickname,
    )
```
- `age` query parameter is a required `int`
    - if none is provided the response contains: 
        ```json
        {
          "validation_error": {
            "query_params": [
              {
                "loc": [
                  "age"
                ],
                "msg": "field required",
                "type": "value_error.missing"
              }
            ]
          }
        }
        ```
    - for incompatible type (e. g. string `/?age=not_a_number`)
        ```json
        {
          "validation_error": {
            "query_params": [
              {
                "loc": [
                  "age"
                ],
                "msg": "value is not a valid integer",
                "type": "type_error.integer"
              }
            ]
          }
        }
        ```
- likewise for body parameters
- example call with valid parameters:
``curl -XPOST http://localhost:5000/?age=20 --data '{"name": "John Doe"}' -H 'Content-Type: application/json'``

-> ``{"id": 2, "age": 20, "name": "John Doe", "nickname": null}``

### Modify response status code
The default success status code is `200`. It can be modified in two ways
- in return statement
```python
# necessary imports, app and models definition
...

@app.route("/", methods=["POST"])
@validate(body=BodyModel, query=QueryModel)
def post():
    return ResponseModel(
            id=id_,
            age=request.query_params.age,
            name=request.body_params.name,
            nickname=request.body_params.nickname,
        ), 201
```
- in `validate` decorator
```python
@app.route("/", methods=["POST"])
@validate(body=BodyModel, query=QueryModel, on_success_status=201)
def post():
    ...
```

### Example app
For more complete examples see [example application](https://github.com/bauerji/flask_pydantic/tree/master/example_app).

## Contributing
Feature requests and pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

- clone repository
    ```bash
    git clone https://github.com/bauerji/flask_pydantic.git
    cd flask_pydantic
    ```
 - create virtual environment and activate it
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
 - install development requirements
    ```bash
    python3 -m pip install -r requirements/test.pip
    ```
 - checkout new branch and make your desired changes (don't forget to update tests)
    ```bash
    git checkout -b <your_branch_name>
    ```
 - run tests
    ```bash
    python3 -m pytest
    ```
 - if tests fails on Black tests, make sure You have your code compliant with style of [Black formatter](https://github.com/psf/black)
 - push your changes and create a pull request to master branch

## TODOs:
- header request parameters
- cookie request parameters
