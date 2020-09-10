# Release history

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
