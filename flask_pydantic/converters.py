from typing import Type, List, Optional, Union, TypeVar

from pydantic import BaseModel
from werkzeug.datastructures import ImmutableMultiDict

T = TypeVar('T')
def is_list_or_optional_list(field_type: Type[T]) -> bool:
    """Check if the field type is List or Optional[List]."""
    # Check if the field is a List
    if getattr(field_type, '_name', None) == 'List':
        return True

    # Check if the field is an Optional[List]
    if hasattr(field_type, '__args__'):
        return any(getattr(arg, '_name', None) == 'List' for arg in field_type.__args__)

    return False

def convert_query_params(
    query_params: ImmutableMultiDict, model: Type[BaseModel]
) -> dict:
    """
    group query parameters into lists if model defines them

    :param query_params: flasks request.args
    :param model: query parameter's model
    :return: resulting parameters
    """
    return{
        **query_params.to_dict(),
        **{
            key: value
            for key, value in query_params.to_dict(flat=False).items()
            if key in model.model_fields and is_list_or_optional_list(model.__annotations__[key])
        },
    }