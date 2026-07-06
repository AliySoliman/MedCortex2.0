import pytest


def test_conversations_api(client, auth_headers):
    # 1. Create Conversation
    response = client.post(
        "/conversations",
        json={"title": "Web API Test Conversation"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    conv = response.json()
    assert conv["id"] is not None
    assert conv["title"] == "Web API Test Conversation"

    # 2. List Conversations
    response = client.get("/conversations", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(c["id"] == conv["id"] for c in data["conversations"])

    # 3. Get Stats
    response = client.get("/conversations/stats", headers=auth_headers)
    assert response.status_code == 200
    stats = response.json()
    assert stats["active_conversations"] >= 1

    # 4. Get Conversation By ID
    response = client.get(f"/conversations/{conv['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Web API Test Conversation"

    # 5. Patch Conversation
    response = client.patch(
        f"/conversations/{conv['id']}",
        json={"title": "Patched Title"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Patched Title"

    # 6. Delete Conversation
    response = client.delete(f"/conversations/{conv['id']}", headers=auth_headers)
    assert response.status_code == 204


def test_messages_api(client, auth_headers):
    # Create conversation first
    response = client.post(
        "/conversations",
        json={"title": "Message API Test"},
        headers=auth_headers,
    )
    conv_id = response.json()["id"]

    # 1. Post message to conversation
    response = client.post(
        f"/messages?conversation_id={conv_id}",
        json={"role": "user", "content": "Hello, doctor!"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    msg = response.json()
    assert msg["content"] == "Hello, doctor!"

    # 2. List messages
    response = client.get(f"/messages?conversation_id={conv_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["messages"][0]["id"] == msg["id"]


def test_history_favorites_feedback_api(client, auth_headers):
    # Create conversation and message first
    response = client.post(
        "/conversations",
        json={"title": "Flu symptoms query"},
        headers=auth_headers,
    )
    conv_id = response.json()["id"]

    response = client.post(
        f"/messages?conversation_id={conv_id}",
        json={"role": "user", "content": "I think I have the flu"},
        headers=auth_headers,
    )
    msg_id = response.json()["id"]

    # 1. History Search
    response = client.get("/history/search?q=flu", headers=auth_headers)
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    assert results[0]["conversation_id"] == conv_id

    # 2. Favorites
    response = client.post(
        "/favorites",
        json={"message_id": msg_id, "note": "Important symptoms description"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    fav = response.json()
    assert fav["message_id"] == msg_id
    assert fav["note"] == "Important symptoms description"

    # 3. Feedback
    response = client.post(
        "/feedback",
        json={"message_id": msg_id, "rating": 5, "comment": "Excellent AI"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    fb = response.json()
    assert fb["message_id"] == msg_id
    assert fb["rating"] == 5
