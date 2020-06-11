# Release history

## 0.0.5 (2020-01-15)
### Bugfixes
- do not try to access query or body requests parameters unless model is provided


## 0.0.6 (2020-06-11)
### Features
- return `415 - Unsupported media type` response for requests to endpoints with specified body model with other content type than `application/json`.
