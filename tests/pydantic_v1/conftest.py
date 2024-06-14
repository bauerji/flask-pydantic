"""
Specific confest.py file for testing behavior with Pydantic V1.

The fixtures below override the confest.py's fixtures for this module only.
"""

from typing import List, Optional, Type

import pytest

from pydantic.v1 import BaseModel


@pytest.fixture
def query_model() -> Type[BaseModel]:
    class Query(BaseModel):
        limit: int = 2
        min_views: Optional[int] = None

    return Query


@pytest.fixture
def body_model() -> Type[BaseModel]:
    class Body(BaseModel):
        search_term: str
        exclude: Optional[str] = None

    return Body


@pytest.fixture
def form_model() -> Type[BaseModel]:
    class Form(BaseModel):
        search_term: str
        exclude: Optional[str] = None

    return Form


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
