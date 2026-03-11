from fastapi.testclient import TestClient
from src.api.main import app
import pytest

client = TestClient(app)


@pytest.mark.parametrize("input_request, status_code, expected_score", [
    ({'surface_reelle_bati': 60, 'nombre_pieces_principales': 2, 'code_departement': '15', 'type_local': 'Appartment'}, 200, None),
])

def test_scoring_api(input_request, status_code, expected_score):
    response = client.post("/scoring/", json=input_request)
    assert response.status_code == status_code

    if expected_score is not None:
        assert response.json() == {"score": expected_score}
