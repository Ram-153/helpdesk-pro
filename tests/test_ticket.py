def register_and_login(client, name, email, password="Test@123"):
    register_response = client.post(
        "/api/auth/register",
        json={
            "name": name,
            "email": email,
            "password": password
        }
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": password
        }
    )

    assert login_response.status_code == 200

    return login_response.get_json()["access_token"]


def test_create_ticket_success(client):
    token = register_and_login(
        client,
        "Ticket Customer",
        "ticket@test.com"
    )

    response = client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Internet connection problem",
            "description": "Internet is not working",
            "category": "Network"
        }
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["message"] == "Ticket created successfully"
    assert data["ticket"]["title"] == "Internet connection problem"
    assert data["ticket"]["status"] == "OPEN"
    assert data["ticket"]["priority"] == "MEDIUM"
    assert data["ticket"]["category"] == "Network"


def test_create_ticket_invalid_priority(client):
    token = register_and_login(
        client,
        "Priority Customer",
        "priority@test.com"
    )

    response = client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Invalid priority ticket",
            "description": "Testing invalid priority",
            "priority": "CRITICAL"
        }
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "Invalid priority"


def test_create_ticket_requires_authentication(client):
    response = client.post(
        "/api/tickets",
        json={
            "title": "Unauthenticated ticket",
            "description": "This should fail"
        }
    )

    assert response.status_code == 401


def test_get_customer_tickets(client):
    token = register_and_login(
        client,
        "List Customer",
        "list@test.com"
    )

    client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "First ticket",
            "description": "First ticket description"
        }
    )

    client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Second ticket",
            "description": "Second ticket description",
            "priority": "HIGH"
        }
    )

    response = client.get(
        "/api/tickets",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200

    data = response.get_json()

    assert len(data["tickets"]) == 2


def test_get_single_ticket(client):
    token = register_and_login(
        client,
        "Single Ticket Customer",
        "single@test.com"
    )

    create_response = client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Specific ticket",
            "description": "Specific ticket description"
        }
    )

    ticket_id = create_response.get_json()["ticket"]["id"]

    response = client.get(
        f"/api/tickets/{ticket_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["ticket"]["id"] == ticket_id
    assert data["ticket"]["title"] == "Specific ticket"


def test_customer_cannot_view_another_customers_ticket(client):
    owner_token = register_and_login(
        client,
        "Ticket Owner",
        "owner@test.com"
    )

    other_token = register_and_login(
        client,
        "Other Customer",
        "other@test.com"
    )

    create_response = client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "title": "Private ticket",
            "description": "Private ticket description"
        }
    )

    ticket_id = create_response.get_json()["ticket"]["id"]

    response = client.get(
        f"/api/tickets/{ticket_id}",
        headers={"Authorization": f"Bearer {other_token}"}
    )

    assert response.status_code == 403

    data = response.get_json()

    assert data["error"] == "Access denied"


def test_create_ticket_missing_required_fields(client):
    token = register_and_login(
        client,
        "Missing Fields Customer",
        "missing@test.com"
    )

    response = client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Missing description"
        }
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "title and description are required"
