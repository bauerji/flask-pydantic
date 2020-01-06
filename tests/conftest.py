from typing import Type, Optional, List

import pytest
from flask import Flask, request
from flask_pydantic import validate
from pydantic import BaseModel


@pytest.fixture
def posts() -> List[dict]:
    return [
        {"title": "title 1", "text": "random text", "views": 10},
        {"title": "2", "text": "another text", "views": 2},
        {"title": "3", "text": "longer text than usual", "views": 4},
        {"title": "title 13", "text": "nothing", "views": 5},
    ]


@pytest.fixture
def query_model() -> Type[BaseModel]:
    class Query(BaseModel):
        limit: int = 2
        min_views: Optional[int]

    return Query


@pytest.fixture
def body_model() -> Type[BaseModel]:
    class Body(BaseModel):
        search_term: str
        exclude: Optional[str]

    return Body


@pytest.fixture
def post_model() -> Type[BaseModel]:
    class Post(BaseModel):
        title: str
        text: str
        views: int

    return Post


@pytest.fixture
def response_model(post_model: BaseModel) -> Type[BaseModel]:
    class Response(BaseModel):
        results: List[post_model]
        count: int

    return Response


def is_excluded(post: dict, exclude: Optional[str]) -> bool:
    if exclude is None:
        return False
    return post["title"].contains(exclude) or post["text"].contains(exclude)


def pass_search(
    post: dict, search_term: str, exclude: Optional[str], min_views: Optional[int]
) -> bool:
    return (
        (post["title"].contains(search_term) or post["text"].contains(search_term))
        and not is_excluded(post, exclude)
        and (min_views is None or post["views"] >= min_views)
    )


@pytest.fixture
def app(posts, response_model, query_model, body_model):
    app = Flask("test_app")

    @app.route("/search", methods=["POST"])
    @validate(query=query_model, body=body_model)
    def post(query):
        query_params = request.query_params
        body = request.body_params
        print(query_params)
        print(body)
        results = [
            p
            for p in posts
            if pass_search(p, body.search_term, body.exclude, query_params.min_views)
        ][:query_params]
        print(results)
        return response_model(results=results, count=len(results))

    return app
