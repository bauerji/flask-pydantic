from typing import Type

from pydantic import BaseModel
from werkzeug.datastructures import ImmutableMultiDict
from pydantic_settings.sources import PydanticBaseSettingsSource, EnvSettingsSource
from pydantic_settings.main import BaseSettings


def convert_query_params(
    query_params: ImmutableMultiDict, model: Type[BaseModel]
) -> dict:
    """
    group query parameters into lists if model defines them

    :param query_params: flasks request.args
    :param model: query parameter's model
    :return: resulting parameters
    """
    abstract_base_setting = BaseSettings()
    concrete_base_setting = EnvSettingsSource(settings_cls= abstract_base_setting)
    return {
        **query_params.to_dict(),
        **{
            key: value
            for key, value in query_params.to_dict(flat=False).items()
            #todo: all this needs to check is if something is of a list or not,
            if key in model.model_fields and concrete_base_setting.field_is_complex(model.model_fields[key])
        },
    }
