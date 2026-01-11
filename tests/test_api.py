import pytest
from fastapi import status

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert "status" in response.json()

def test_query_endpoint(client, sample_query):
    response = client.post("/query", json=sample_query)
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_503_SERVICE_UNAVAILABLE]

def test_query_validation(client):
    response = client.post("/query", json={"question": ""})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
