"""
Test the health check endpoint
"""
import pytest


def test_health_endpoint(client):
    """Test that the health endpoint returns correct response"""

    response = client.get('/health')
    assert response.status_code == 200

    data = response.get_json()
    assert data == {'status': 'healthy'}


def test_health_endpoint_content_type(client):
    """Test that health endpoint returns JSON content type"""

    response = client.get('/health')
    assert response.status_code == 200
    assert response.content_type == 'application/json'


def test_health_endpoint_get_only(client):
    """Test that health endpoint only accepts GET requests"""

    # POST should not be allowed
    response = client.post('/health')
    assert response.status_code == 405  # Method Not Allowed

    # PUT should not be allowed
    response = client.put('/health')
    assert response.status_code == 405

    # DELETE should not be allowed
    response = client.delete('/health')
    assert response.status_code == 405
