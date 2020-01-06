import pytest


test_cases = [
    pytest.param(
        "?limit=limit",
        {"search_term": "text"},
        400,
        {
            "validation_error": {
                "query_params": [
                    {
                        "loc": ["limit"],
                        "msg": "value is not a valid integer",
                        "type": "type_error.integer",
                    }
                ]
            }
        },
        id="invalid limit",
    ),
    pytest.param(
        "?limit=2",
        {},
        400,
        {
            "validation_error": {
                "body_params": [
                    {
                        "loc": ["search_term"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    }
                ]
            }
        },
        id="missing required body parameter",
    ),
]


class TestSimple:
    @pytest.mark.parametrize("query,body,expected_status,expected_response", test_cases)
    def test_post(self, client, query, body, expected_status, expected_response):
        response = client.post(f"/search{query}", json=body)
        assert response.json == expected_response
        assert response.status_code == expected_status
