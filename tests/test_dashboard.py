from app.extensions import db
from app.models.user import User


def register_and_login(client, name, email, password, role="customer"):
    register_response = client.post(
        "/api/auth/register",
        json={
            "name": name,
            "email": email,
            "password": password
        }
    )

    assert register_response.status_code == 201

    if role != "customer":
        user = User.query.filter_by(email=email).first()

        assert user is not None

        user.role = role
        db.session.commit()

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": password
        }
    )

    assert login_response.status_code == 200

    return login_response.get_json()["access_token"]


def create_ticket(client, token, title, priority="MEDIUM", category="Technical"):
    response = client.post(
        "/api/tickets",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "title": title,
            "description": f"Description for {title}",
            "category": category,
            "priority": priority
        }
    )

    assert response.status_code == 201

    return response.get_json()["ticket"]["id"]


def test_dashboard_summary(client):
    token = register_and_login(
        client,
        "Dashboard Agent",
        "dashboard_agent@test.com",
        "Test@123",
        role="agent"
    )

    create_ticket(
        client,
        token,
        "High Priority Ticket",
        priority="HIGH"
    )

    response = client.get(
        "/api/dashboard/summary",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["total_tickets"] == 1
    assert data["open_tickets"] == 1
    assert data["high_priority_tickets"] == 1


def test_dashboard_statistics(client):
    token = register_and_login(
        client,
        "Statistics Agent",
        "statistics_agent@test.com",
        "Test@123",
        role="agent"
    )

    create_ticket(
        client,
        token,
        "Network Issue",
        priority="HIGH",
        category="Network"
    )

    create_ticket(
        client,
        token,
        "Software Issue",
        priority="LOW",
        category="Software"
    )

    response = client.get(
        "/api/dashboard/statistics",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["by_status"]["OPEN"] == 2
    assert data["by_priority"]["HIGH"] == 1
    assert data["by_priority"]["LOW"] == 1
    assert data["by_category"]["Network"] == 1
    assert data["by_category"]["Software"] == 1


def test_recent_tickets(client):
    token = register_and_login(
        client,
        "Recent Agent",
        "recent_agent@test.com",
        "Test@123",
        role="agent"
    )

    create_ticket(
        client,
        token,
        "First Ticket"
    )

    create_ticket(
        client,
        token,
        "Second Ticket"
    )

    response = client.get(
        "/api/dashboard/recent-tickets?limit=1",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["count"] == 1
    assert len(data["tickets"]) == 1


def test_filter_tickets_by_priority(client):
    token = register_and_login(
        client,
        "Filter Agent",
        "filter_agent@test.com",
        "Test@123",
        role="agent"
    )

    create_ticket(
        client,
        token,
        "High Ticket",
        priority="HIGH"
    )

    create_ticket(
        client,
        token,
        "Low Ticket",
        priority="LOW"
    )

    response = client.get(
        "/api/dashboard/tickets?priority=HIGH",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert len(data["tickets"]) == 1
    assert data["tickets"][0]["priority"] == "HIGH"


def test_dashboard_requires_authentication(client):
    response = client.get("/api/dashboard/summary")

    assert response.status_code == 401


def test_customer_cannot_access_dashboard(client):
    token = register_and_login(
        client,
        "Dashboard Customer",
        "dashboard_customer@test.com",
        "Test@123"
    )

    response = client.get(
        "/api/dashboard/summary",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 403
