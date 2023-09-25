from dataclasses import dataclass
from typing import Optional

from flask import Flask, jsonify, request
from flask_pydantic import validate
from pydantic import BaseModel

app = Flask("flask_pydantic_app")


@dataclass
class Config:
    FLASK_PYDANTIC_VALIDATION_ERROR_STATUS_CODE: int = 422


app.config.from_object(Config)


class QueryModel(BaseModel):
    age: int


class IndexParam(BaseModel):
    index: int


class BodyModel(BaseModel):
    name: str
    nickname: Optional[str] = None


class FormModel(BaseModel):
    name: str
    nickname: Optional[str] = None


class ResponseModel(BaseModel):
    id: int
    age: int
    name: str
    nickname: Optional[str] = None


@app.route("/", methods=["POST"])
@validate(body=BodyModel, query=QueryModel)
def post():
    """
    Basic example with both query and body parameters, response object serialization.
    """
    # save model to DB
    id_ = 2

    return ResponseModel(
        id=id_,
        age=request.query_params.age,
        name=request.body_params.name,
        nickname=request.body_params.nickname,
    )


@app.route("/form", methods=["POST"])
@validate(form=FormModel, query=QueryModel)
def form_post():
    """
    Basic example with both query and form-data parameters, response object serialization.
    """
    # save model to DB
    id_ = 2

    return ResponseModel(
        id=id_,
        age=request.query_params.age,
        name=request.form_params.name,
        nickname=request.form_params.nickname,
    )


@app.route("/kwargs", methods=["POST"])
@validate()
def post_kwargs(body: BodyModel, query: QueryModel):
    """
    Basic example with both query and body parameters, response object serialization.
    This time using the decorated function kwargs `body` and `query` type hinting
    """
    # save model to DB
    id_ = 3

    return ResponseModel(id=id_, age=query.age, name=body.name, nickname=body.nickname)


@app.route("/form/kwargs", methods=["POST"])
@validate()
def form_post_kwargs(form: FormModel, query: QueryModel):
    """
    Basic example with both query and form-data parameters, response object serialization.
    This time using the decorated function kwargs `form` and `query` type hinting
    """
    # save model to DB
    id_ = 3

    return ResponseModel(id=id_, age=query.age, name=form.name, nickname=form.nickname)


@app.route("/many", methods=["GET"])
@validate(response_many=True)
def get_many():
    """
    This route returns response containing many serialized objects.
    """
    return [
        ResponseModel(id=1, age=95, name="Geralt", nickname="White Wolf"),
        ResponseModel(id=2, age=45, name="Triss Merigold", nickname="sorceress"),
        ResponseModel(id=3, age=42, name="Julian Alfred Pankratz", nickname="Jaskier"),
        ResponseModel(id=4, age=101, name="Yennefer", nickname="Yenn"),
    ]


@app.route("/select", methods=["POST"])
@validate(request_body_many=True, query=IndexParam, body=BodyModel)
def select_from_array():
    """
    This route takes array of objects in request body and returns the object on index
    (index is a url query parameter)
    """
    try:
        return BodyModel(**request.body_params[request.query_params.index].dict())
    except IndexError:
        return jsonify({"reason": "index out of bound"}), 400
