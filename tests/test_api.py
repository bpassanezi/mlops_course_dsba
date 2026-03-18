"""
Unit tests for the FastAPI application.

Why unit tests?
  - They verify that individual API endpoints route and validate data correctly.
  - When someone on the team refactors the routes or controllers, 
    the tests catch regressions immediately (e.g., breaking API contracts).
"""

import sys
import os

# Add the src/ folder to the Python path so that "from api.main" works
# exactly as it does when running inside src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI app we want to test
from api.main import app

client = TestClient(app)


class TestScoringAPI:
    """Tests for the prediction scoring endpoints."""

    @pytest.mark.parametrize("input_request, status_code, expected_score", [
        (
            {
                'surface_reelle_bati': 60, 
                'nombre_pieces_principales': 2, 
                'code_departement': '15', 
                'type_local': 'Appartement'
            }, 
            200, 
            None
        ),
        (
            {
                'surface_reelle_bati': 80, 
                'nombre_pieces_principales': 3, 
                'code_departement': '75', 
                'type_local': 'Maison'
            }, 
            200, 
            None
        ),
        # Invalid request
        (
            {
                'surface_reelle_bati': 80, 
                'nombre_pieces_principales': 3, 
                'code_departement': None, 
                'type_local': None
            }, 
            422, 
            None
        ),
    ])
    def test_scoring_api_responses(self, input_request, status_code, expected_score):
        """The /scoring/ endpoint should return valid statuses for various payloads."""
        response = client.post("/scoring/", json=input_request)
        
        # Verify status code matches
        assert response.status_code == status_code

        # If a precise expected score is provided, assert exact equality
        if expected_score is not None:
            assert response.json() == {"score": expected_score}
            
        # Otherwise, if it is a 200 OK, ensure it conforms to the response schema
        elif status_code == 200:
            data = response.json()
            assert "score" in data
            assert isinstance(data["score"], (int, float))
            assert "breakdown" in data
            assert "dept_stats" in data
