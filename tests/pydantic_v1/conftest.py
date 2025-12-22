"""
Specific confest.py file for testing behavior with Pydantic V1.

The fixtures below override the confest.py's fixtures for this module only.
"""

import pytest
from pydantic.v1 import BaseModel


@pytest.fixture
def query_model() -> type[BaseModel]:
    class Query(BaseModel):
        limit: int = 2
        min_views: int | None = None

    return Query


@pytest.fixture
def body_model() -> type[BaseModel]:
    class Body(BaseModel):
        search_term: str
        exclude: str | None = None

    return Body


@pytest.fixture
def form_model() -> type[BaseModel]:
    class Form(BaseModel):
        search_term: str
        exclude: str | None = None

    return Form


@pytest.fixture
def post_model() -> type[BaseModel]:
    class Post(BaseModel):
        title: str
        text: str
        views: int

    return Post


@pytest.fixture
def response_model(post_model: BaseModel) -> type[BaseModel]:
    class Response(BaseModel):
        results: list[post_model]
        count: int

    return Response
