def test_health_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["service"] == "enterprise-itsm"


def test_create_app_testing_config(app):
    assert app.config["TESTING"] is True
    assert app.config["WTF_CSRF_ENABLED"] is False
