from typing import Optional
from flask import Flask, request
from pydantic import BaseModel

from flask_pydantic import validate

app = Flask("flask_pydantic_app")

class RequestBodyModel(BaseModel):
	name: str
	nickname: Optional[str]


class QueryModel(BaseModel):
	age: int

@app.route("/", methods=["GET"])
@validate()
def get(query:QueryModel):
	age = query.age
	return ResponseModel(
		age=age,
		id=0, name="abc", nickname="123"
		)

class ResponseModel(BaseModel):
	id: int
	age: int
	name: str
	nickname: Optional[str]

@app.route("/", methods=["POST"])
@validate()
def post(body:RequestBodyModel): 
	name = body.name
	nickname = body.nickname
	return ResponseModel(
		name=name, nickname=nickname,id=0, age=1000
		)

@app.route("/both", methods=["POST"])
@validate()
def get_and_post(body:RequestBodyModel,query:QueryModel):
	name = body.name # From request body
	nickname = body.nickname # From request body
	age = query.age # from query parameters
	return ResponseModel(
		age=age, name=name, nickname=nickname,
		id=0
	)

app.run(debug=True)