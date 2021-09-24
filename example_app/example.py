from typing import Optional

from flask import Flask
from pydantic import BaseModel

from flask_pydantic import validate, add_openapi_spec, openapi_docs

app = Flask("flask_pydantic_app")


class RequestBodyModel(BaseModel):
    name: str
    nickname: Optional[str]


class QueryModel(BaseModel):
    age: int


@app.route("/", methods=["GET"])
@validate()
def get(query: QueryModel):
    age = query.age
    return ResponseModel(age=age, id=0, name="abc", nickname="123")


"""
curl --location --request GET 'http://127.0.0.1:5000/'
curl --location --request GET 'http://127.0.0.1:5000/?ageeee=5'
curl --location --request GET 'http://127.0.0.1:5000/?age=abc'

curl --location --request GET 'http://127.0.0.1:5000/?age=5'
"""


class ResponseModel(BaseModel):
    id: int
    age: int
    name: str
    nickname: Optional[str]


@app.route("/character/<character_id>/", methods=["GET"])
@validate()
def get_character(character_id: int):
    characters = [
        ResponseModel(id=1, age=95, name="Geralt", nickname="White Wolf"),
        ResponseModel(id=2, age=45, name="Triss Merigold", nickname="sorceress"),
        ResponseModel(id=3, age=42, name="Julian Alfred Pankratz", nickname="Jaskier"),
        ResponseModel(id=4, age=101, name="Yennefer", nickname="Yenn"),
    ]
    try:
        return characters[character_id]
    except IndexError:
        return {"error": "Not found"}, 400


"""
curl http://127.0.0.1:5000/character/2/ \
--header 'Content-Type: application/json'
"""


@app.route("/", methods=["POST"])
@openapi_docs()
@validate()
def post(body: RequestBodyModel):
    name = body.name
    nickname = body.nickname
    return ResponseModel(name=name, nickname=nickname, id=0, age=1000)


"""
curl --location --request POST 'http://127.0.0.1:5000/'

curl --location --request POST 'http://127.0.0.1:5000/' \
--header 'Content-Type: application/json' \
--data-raw '{'

curl --location --request POST 'http://127.0.0.1:5000/' \
--header 'Content-Type: application/json' \
--data-raw '{"nameee":123}'

curl --location --request POST 'http://127.0.0.1:5000/' \
--header 'Content-Type: application/json' \
--data-raw '{"name":123}'
"""


@app.route("/both", methods=["POST"])
@validate()
def get_and_post(body: RequestBodyModel, query: QueryModel):
    name = body.name  # From request body
    nickname = body.nickname  # From request body
    age = query.age  # from query parameters
    return ResponseModel(age=age, name=name, nickname=nickname, id=0)


"""
curl --location --request POST 'http://127.0.0.1:5000/both' \
--header 'Content-Type: application/json' \
--data-raw '{"name":123}'

curl --location --request POST 'http://127.0.0.1:5000/both?age=40' \
--header 'Content-Type: application/json' \
--data-raw '{"name":123}'
"""


if __name__ == "__main__":
    add_openapi_spec(app)
    app.run()
