from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

import pytest
from flask import Flask, request
from pydantic import BaseModel
from pydantic.generics import GenericModel

from flask_pydantic import validate


@pytest.fixture
def posts() -> List[Dict[str, Any]]:
    return [
        {"title": "title 1", "text": "random text", "views": 1},
        {"title": "2", "text": "another text", "views": 2},
        {"title": "3", "text": "longer text than usual", "views": 4},
        {"title": "title 13", "text": "nothing", "views": 5},
    ]


class Query(BaseModel):
    limit: int = 2
    min_views: Optional[int]


@pytest.fixture
def query_model() -> Type[BaseModel]:
    return Query


class Body(BaseModel):
    search_term: str
    exclude: Optional[str]


@pytest.fixture
def body_model() -> Type[BaseModel]:
    return Body


class Form(BaseModel):
    search_term: str
    exclude: Optional[str]


@pytest.fixture
def form_model() -> Type[BaseModel]:
    return Form


@pytest.fixture
def post_model() -> Type[BaseModel]:
    class Post(BaseModel):
        title: str
        text: str
        views: int

    return Post


PostModelT = TypeVar("PostModelT", bound=BaseModel)


class Response(GenericModel, Generic[PostModelT]):
    results: List[PostModelT]
    count: int


@pytest.fixture
def response_model(post_model: PostModelT) -> Type[Response[PostModelT]]:
    return Response[PostModelT]


def is_excluded(post: Dict[str, Any], exclude: Optional[str]) -> bool:
    if exclude is None:
        return False
    return exclude in post["title"] or exclude in post["text"]


def pass_search(
    post: Dict[str, Any],
    search_term: str,
    exclude: Optional[str],
    min_views: Optional[int],
) -> bool:
    return (
        (search_term in post["title"] or search_term in post["text"])
        and not is_excluded(post, exclude)
        and (min_views is None or post["views"] >= min_views)
    )


QueryModelT = TypeVar("QueryModelT", bound=Query)
BodyModelT = TypeVar("BodyModelT", bound=Body)
FormModelT = TypeVar("FormModelT", bound=Form)


@pytest.fixture
def app(
    posts: List[Dict[str, Any]],
    response_model: Type[Response[PostModelT]],
    query_model: Type[QueryModelT],
    body_model: Type[BodyModelT],
    post_model: Type[PostModelT],
    form_model: Type[FormModelT],
) -> Flask:
    app = Flask("test_app")
    app.config["DEBUG"] = True
    app.config["TESTING"] = True

    @app.route("/search", methods=["POST"])
    @validate(query=query_model, body=body_model)
    def post():
        query_params = request.query_params
        body: BodyModelT = request.body_params
        results = [
            post_model(**p)
            for p in posts
            if pass_search(p, body.search_term, body.exclude, query_params.min_views)
        ]
        return response_model(results=results[: query_params.limit], count=len(results))

    @app.route("/search/kwargs", methods=["POST"])
    @validate()
    def post_kwargs(query: Type[QueryModelT], body: Type[BodyModelT]):
        results = [
            post_model(**p)
            for p in posts
            if pass_search(p, body.search_term, body.exclude, query.min_views)
        ]
        return response_model(results=results[: query.limit], count=len(results))

    @app.route("/search/form/kwargs", methods=["POST"])
    @validate()
    def post_kwargs_form(query: Type[QueryModelT], form: Type[BodyModelT]):
        results = [
            post_model(**p)
            for p in posts
            if pass_search(p, form.search_term, form.exclude, query.min_views)
        ]
        return response_model(results=results[: query.limit], count=len(results))

    return app
