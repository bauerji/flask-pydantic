from typing import Type, Union

try:
    from typing import get_args, get_origin
except ImportError:
    from typing_extensions import get_args, get_origin

from pydantic import BaseModel
from pydantic.v1 import BaseModel as V1BaseModel
from werkzeug.datastructures import ImmutableMultiDict

V1OrV2BaseModel = Union[BaseModel, V1BaseModel]


def _is_list(type_: Type) -> bool:
    origin = get_origin(type_)
    if origin is list:
        return True
    if origin is Union:
        return any(_is_list(t) for t in get_args(type_))
    return False


def convert_query_params(
    query_params: ImmutableMultiDict, model: Type[V1OrV2BaseModel]
) -> dict:
    """
    group query parameters into lists if model defines them

    :param query_params: flasks request.args
    :param model: query parameter's model
    :return: resulting parameters
    """
    if issubclass(model, BaseModel):
        return {
            **query_params.to_dict(),
            **{
                key: value
                for key, value in query_params.to_dict(flat=False).items()
                if key in model.model_fields
                and _is_list(model.model_fields[key].annotation)
            },
        }
    else:
        return {
            **query_params.to_dict(),
            **{
                key: value
                for key, value in query_params.to_dict(flat=False).items()
                if key in model.__fields__ and model.__fields__[key].is_complex()
            },
        }
