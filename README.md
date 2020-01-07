# Flask-Pydantic
Flask extension for integration with the awesome [pydantic package](https://github.com/samuelcolvin/pydantic) with [Flask](https://palletsprojects.com/p/flask/).

## Basics
`validate` decorator validates query and body request parameters and makes them accessible via flask's `request` variable

| **parameter type** | **`request` attribute name** |
|:--------------:|:------------------------:|
| query          | `query_params`           |
| body           | `body_params`            |

Success response status code can be modified via `on_success_status` parameter of `validate` decorator.

If validation fails, `400` response is returned with failure explanation.

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

## TODOs:
- iterable of objects
    - in request body
- header request parameters
- cookie request parameters
