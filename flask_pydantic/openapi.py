import inspect
from typing import Optional
from flask import Flask, Blueprint, render_template, jsonify, abort
from flask.views import MethodView
from werkzeug.routing import parse_rule, parse_converter_args

OPENAPI_VERSION = "3.0.2"
OPENAPI_INFO = dict(
    title="Service Documents",
    version="latest",
)

OPENAPI_NAME = "docs"
OPENAPI_ENDPOINT = "/docs/"
OPENAPI_URL_PREFIX = None
OPENAPI_MODE = "normal"

OPENAPI_TEMPLATE_FOLDER = "templates"
OPENAPI_FILENAME = "openapi.json"
OPENAPI_UI = "swagger"


def add_openapi_spec(
    app: Flask,
    endpoint: str = OPENAPI_ENDPOINT,
    url_prefix: Optional[str] = OPENAPI_URL_PREFIX,
    template_folder: str = OPENAPI_TEMPLATE_FOLDER,
    openapi_filename: str = OPENAPI_FILENAME,
    mode: str = OPENAPI_MODE,
    ui: str = OPENAPI_UI,
    extra_props: dict = {},
):
    assert isinstance(app, Flask)
    assert mode in {"normal", "greedy", "strict"}

    if not hasattr(add_openapi_spec, "openapi"):
        add_openapi_spec.openapi = OpenAPI(app)
    openapi = add_openapi_spec.openapi
    openapi.extra_props = extra_props

    name = OPENAPI_NAME
    blueprint = Blueprint(
        name, __name__, url_prefix=url_prefix, template_folder=template_folder
    )
    blueprint.add_url_rule(
        endpoint,
        name,
        view_func=APIView().as_view(
            name, view_args=dict(ui=ui, filename=openapi_filename)
        ),
    )

    # docs/openapi.json
    @blueprint.route(f"{endpoint}<filename>")
    def ___jsonfile___(filename):
        if openapi_filename == filename:
            return jsonify(openapi.spec)
        abort(404)

    app.register_blueprint(blueprint)


class APIView(MethodView):
    def __init__(self, *args, **kwargs):
        view_args = kwargs.pop("view_args", {})
        self.ui = view_args.get("ui")
        self.filename = view_args.get("filename")
        super().__init__(*args, **kwargs)

    def get(self):
        assert self.ui in {"redoc", "swagger"}
        ui_file = f"{self.ui}.html"
        return render_template(ui_file, spec_url=self.filename)


class APIError:
    def __init__(self, code: int, msg: str) -> None:
        self.code = code
        self.msg = msg

    def __repr__(self) -> str:
        return f"{self.code} {self.msg}"


class OpenAPI:
    _models = {}

    def __init__(self, app: Flask) -> None:
        assert isinstance(app, Flask)

        self.app = app
        self.endpoint: str = OPENAPI_ENDPOINT
        self.mode: str = OPENAPI_MODE
        self.openapi_version: str = OPENAPI_VERSION
        self.info: dict = OPENAPI_INFO
        self.extra_props: dict = {}

        self._spec = None

    @property
    def spec(self):
        if self._spec is None:
            self._spec = self.generate_spec()
        return self._spec

    def _bypass(self, func):
        if self.mode == "greedy":
            return False
        elif self.mode == "strict":
            if getattr(func, "_openapi", None) == self.__class__:
                return False
            return True
        else:
            decorator = getattr(func, "_openapi", None)
            if decorator and decorator != self.__class__:
                return True
            return False

    def generate_spec(self):
        """
        generate OpenAPI spec JSON file
        """

        routes = {}
        tags = {}

        for rule in self.app.url_map.iter_rules():
            if str(rule).startswith(self.endpoint) or str(rule).startswith("/static"):
                continue

            func = self.app.view_functions[rule.endpoint]
            path, parameters = parse_url(str(rule))

            # bypass the function decorated by others
            if self._bypass(func):
                continue

            # multiple methods (with different func) may bond to the same path
            if path not in routes:
                routes[path] = {}

            for method in rule.methods:
                if method in ["HEAD", "OPTIONS"]:
                    continue

                if hasattr(func, "tags"):
                    for tag in func.tags:
                        if tag not in tags:
                            tags[tag] = {"name": tag}

                summary, desc = get_summary_desc(func)
                spec = {
                    "summary": summary or func.__name__.capitalize(),
                    "description": desc or "",
                    "operationID": func.__name__ + "__" + method.lower(),
                    "tags": getattr(func, "tags", []),
                }

                if hasattr(func, "body"):
                    spec["requestBody"] = {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": f"#/components/schemas/{func.body}"}
                            }
                        }
                    }

                params = parameters[:]
                if hasattr(func, "query"):
                    params.append(
                        {
                            "name": func.query,
                            "in": "query",
                            "required": True,
                            "schema": {
                                "$ref": f"#/components/schemas/{func.query}",
                            },
                        }
                    )
                spec["parameters"] = params

                spec["responses"] = {}
                has_2xx = False
                if hasattr(func, "exceptions"):
                    for code, msg in func.exceptions.items():
                        if code.startswith("2"):
                            has_2xx = True
                        spec["responses"][code] = {
                            "description": msg,
                        }

                if hasattr(func, "response"):
                    spec["responses"]["200"] = {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": f"#/components/schemas/{func.response}"
                                }
                            }
                        },
                    }
                elif not has_2xx:
                    spec["responses"]["200"] = {"description": "Successful Response"}

                if any(
                    [hasattr(func, schema) for schema in ("query", "body", "response")]
                ):
                    spec["responses"]["400"] = {
                        "description": "Validation Error",
                    }

                routes[path][method.lower()] = spec

        definitions = {}
        for _, schema in self._models.items():
            if "definitions" in schema:
                for key, value in schema["definitions"].items():
                    definitions[key] = value
                del schema["definitions"]

        data = {
            "openapi": self.openapi_version,
            "info": self.info,
            "tags": list(tags.values()),
            "paths": {**routes},
            "components": {
                "schemas": {name: schema for name, schema in self._models.items()},
            },
            "definitions": definitions,
            **self.extra_props,
        }

        return data

    @classmethod
    def add_model(cls, model):
        cls._models[model.__name__] = model.schema()


def get_summary_desc(func):
    """
    get summary, description from `func.__doc__`

    Summary and description are split by '\n\n'. If only one is provided,
    it will be used as summary.
    """
    doc = inspect.getdoc(func)
    if not doc:
        return None, None
    doc = doc.split("\n\n", 1)
    if len(doc) == 1:
        return doc[0], None
    return doc


def get_converter_schema(converter: str, *args, **kwargs):
    """
    get json schema for parameters in url based on following converters
    https://werkzeug.palletsprojects.com/en/0.15.x/routing/#builtin-converter
    """
    if converter == "any":
        return {"type": "array", "items": {"type": "string", "enum": args}}
    elif converter == "int":
        return {
            "type": "integer",
            "format": "int32",
            **{
                f"{prop}imum": kwargs[prop] for prop in ["min", "max"] if prop in kwargs
            },
        }
    elif converter == "float":
        return {"type": "number", "format": "float"}
    elif converter == "uuid":
        return {"type": "string", "format": "uuid"}
    elif converter == "path":
        return {"type": "string", "format": "path"}
    elif converter == "string":
        return {
            "type": "string",
            **{
                prop: kwargs[prop]
                for prop in ["length", "maxLength", "minLength"]
                if prop in kwargs
            },
        }
    else:
        return {"type": "string"}


def parse_url(path: str):
    """
    Parsing Flask route url to get the normal url path and parameter type.

    Based on Werkzeug_ builtin converters.

    .. _werkzeug: https://werkzeug.palletsprojects.com/en/0.15.x/routing/#builtin-converters
    """
    subs = []
    parameters = []

    for converter, arguments, variable in parse_rule(path):
        if converter is None:
            subs.append(variable)
            continue
        subs.append(f"{{{variable}}}")

        args, kwargs = [], {}

        if arguments:
            args, kwargs = parse_converter_args(arguments)

        schema = get_converter_schema(converter, *args, **kwargs)

        parameters.append(
            {
                "name": variable,
                "in": "path",
                "required": True,
                "schema": schema,
            }
        )

    return "".join(subs), parameters
