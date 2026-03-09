from fastapi.testclient import TestClient
from api.main import app
import pytest

client = TestClient(app)


@pytest.mark.parametrize("input_request, status_code, expected_score", [
    ({'address': 'my_address', 'surface': 10, 'num_rooms': 2}, 200, 20),
    ({'address': 'my_address', 'surface': 100, 'num_rooms': 2}, 200, 220),
    ({'address': 'my_address', 'surface': 100, 'num_rooms': 3}, 200, 220),
    ({'address': 'my_address', 'surface': 100}, 200, 110),
    # Invalid inputs
    ({'address': 10, 'surface': 100}, 422, None),
    ({'address': 'my_address'}, 422, None),
])

def test_scoring_api(input_request, status_code, expected_score):
    response = client.post("/scoring/", json=input_request)
    assert response.status_code == status_code

    if expected_score is not None:
        assert response.json() == {"score": expected_score}
