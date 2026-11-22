import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_home():
    r = client.get("/")
    assert r.status_code == 200
    assert "NOVA" in r.json()["message"]


def test_chat_greeting():
    r = client.post("/chat", json={"message": "hello"})
    assert r.status_code == 200
    assert r.json()["reply"]


def test_chat_rejects_non_string():
    r = client.post("/chat", json={"message": 123})
    assert r.status_code == 422


def test_chat_empty_message():
    r = client.post("/chat", json={"message": ""})
    assert r.status_code == 200
    assert r.json()["reply"]


def test_memory_remember_and_recall():
    key = "pytest_key"
    client.post("/chat", json={"message": f"remember {key}=pytest_value"})
    r = client.post("/chat", json={"message": f"what is {key}"})
    assert "pytest_value" in r.json()["reply"]


def test_teach_and_recall():
    client.post("/chat", json={"message": "teach: pytest question = pytest answer"})
    r = client.post("/chat", json={"message": "what is the pytest question"})
    assert "pytest answer" in r.json()["reply"]


def test_notifications_endpoint():
    r = client.get("/notifications")
    assert r.status_code == 200
    assert "messages" in r.json()


def test_self_check_endpoint():
    r = client.get("/self-check")
    assert r.status_code == 200
    assert "issues" in r.json()


def test_actions_pending():
    r = client.get("/actions/pending")
    assert r.status_code == 200
    assert "actions" in r.json()


def test_auth_me_anonymous():
    r = client.get("/auth/me")
    assert r.status_code == 200
    assert r.json()["user"] is None


def test_dev_login_and_namespaced_memory():
    r = client.post("/auth/dev-login", json={"name": "Pytest User"})
    assert r.status_code == 200
    assert r.json()["ok"] is True

    authed = TestClient(app)
    # reuse cookie from response
    cookies = r.cookies
    for c in cookies.jar:
        authed.cookies.set(c.name, c.value)

    r2 = authed.get("/auth/me")
    assert r2.json()["user"] is not None

    import time
    ns_key = f"pytest_ns_{int(time.time())}"
    anon = TestClient(app)  # fresh client, no session cookie
    anon.post("/chat", json={"message": f"remember {ns_key}=global_value"})
    r3 = authed.post("/chat", json={"message": f"what is {ns_key}"})
    # namespaced user should NOT see the anonymous/global key
    assert "global_value" not in r3.json()["reply"]
