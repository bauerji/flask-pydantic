# Release history

## 0.12.0 (2024-01-08)
### Features
- Support Pydantic 2. Drop support for Pydantic 1. (thanks to @jkseppan)

## 0.11.0 (2022-09-25)
### Features
- Allow raising `flask_pydantic.ValidationError` by setting `FLASK_PYDANTIC_VALIDATION_ERROR_RAISE=True`

## 0.10.0 (2022-07-31)
### Features
- Add validation for form data
- Handle extra headers returned by route functions

### Internal
- Cleanup pipelines, drop python 3.6 tests, test on MacOS images

## 0.9.0 (2021-10-28)
### Features
- Support for passing parameters to [`flask.Request.get_json`](https://tedboy.github.io/flask/generated/generated/flask.Request.get_json.html) function via `validate`'s `get_json_params` parameter 

### Internal
- Add tests for Python 3.10 to pipeline

## 0.8.0 (2021-05-09)
### Features
- Return `400` response when model's  `__root__` validation fails

## 0.7.2 (2021-04-26)
### Bugfixes
- ignore return-type annotations

## 0.7.1 (2021-04-08)
### Bugfixes
- recognize mime types with character encoding standard

## 0.7.0 (2021-04-05)
### Features
- add support for URL path parameters parsing and validation

## 0.6.3 (2021-03-26)
- do pin specific versions of required packages

## 0.6.2 (2021-03-09)
### Bugfixes
- fix type annotations of decorated method

## 0.6.1 (2021-02-18)
### Bugfixes
- parsing of query parameters in older versions of python 3.6


## 0.6.0 (2021-01-31)
### Features
- improve README, example app
- add support for pydantic's [custom root types](https://pydantic-docs.helpmanual.io/usage/models/#custom-root-types)


## 0.5.0 (2021-01-17)
### Features
- add `Flask` classifier

## 0.4.0 (2020-09-10)
### Features
- add support for [alias feature](https://pydantic-docs.helpmanual.io/usage/model_config/#alias-generator) in response models


## 0.3.0 (2020-09-08)
### Features
- add possibility to specify models using keyword arguments


## 0.2.0 (2020-08-07)
### Features
- add support for python version `3.6`


## 0.1.0 (2020-08-02)
### Features
- add proper parsing and validation of array query parameters


## 0.0.7 (2020-07-20)
- add possibility to configure response status code after `ValidationError` using flask app config value `FLASK_PYDANTIC_VALIDATION_ERROR_STATUS_CODE`


## 0.0.6 (2020-06-11)
### Features
- return `415 - Unsupported media type` response for requests to endpoints with specified body model with other content type than `application/json`.


## 0.0.5 (2020-01-15)
### Bugfixes
- do not try to access query or body requests parameters unless model is provided
