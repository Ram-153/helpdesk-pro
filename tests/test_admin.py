from app.extensions import db
from app.models.user import User


def register_and_login(client, name, email, password):
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


def make_admin(email):
    user = User.query.filter_by(email=email).first()

    assert user is not None

    user.role = "admin"
    db.session.commit()


def make_agent(email):
    user = User.query.filter_by(email=email).first()

    assert user is not None

    user.role = "agent"
    db.session.commit()


def create_ticket(client, token):
    response = client.post(
        "/api/tickets",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "title": "Admin Test Ticket",
            "description": "Testing admin ticket assignment",
            "category": "Technical",
            "priority": "HIGH"
        }
    )

    assert response.status_code == 201

    return response.get_json()["ticket"]["id"]


def test_admin_can_list_users(client):
    admin_token = register_and_login(
        client,
        "Admin User",
        "admin@test.com",
        "Test@123"
    )

    make_admin("admin@test.com")

    response = client.get(
        "/api/admin/users",
        headers={
            "Authorization": f"Bearer {admin_token}"
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert "count" in data
    assert "users" in data
    assert data["count"] >= 1


def test_non_admin_cannot_list_users(client):
    token = register_and_login(
        client,
        "Normal User",
        "normal_admin_test@test.com",
        "Test@123"
    )

    response = client.get(
        "/api/admin/users",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 403

    data = response.get_json()

    assert data["error"] == "Admin access required"


def test_admin_can_create_user(client):
    admin_token = register_and_login(
        client,
        "Create Admin",
        "create_admin@test.com",
        "Test@123"
    )

    make_admin("create_admin@test.com")

    response = client.post(
        "/api/admin/users",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "name": "Created Agent",
            "email": "created_agent@test.com",
            "password": "Test@123",
            "role": "agent"
        }
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["message"] == "User created successfully"
    assert data["user"]["email"] == "created_agent@test.com"
    assert data["user"]["role"] == "agent"


def test_admin_can_get_single_user(client):
    admin_token = register_and_login(
        client,
        "Single Admin",
        "single_admin@test.com",
        "Test@123"
    )

    make_admin("single_admin@test.com")

    register_and_login(
        client,
        "Target User",
        "target_user@test.com",
        "Test@123"
    )

    target_user = User.query.filter_by(
        email="target_user@test.com"
    ).first()

    assert target_user is not None

    response = client.get(
        f"/api/admin/users/{target_user.id}",
        headers={
            "Authorization": f"Bearer {admin_token}"
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["user"]["id"] == target_user.id
    assert data["user"]["email"] == "target_user@test.com"


def test_admin_can_change_user_role(client):
    admin_token = register_and_login(
        client,
        "Role Admin",
        "role_admin@test.com",
        "Test@123"
    )

    make_admin("role_admin@test.com")

    register_and_login(
        client,
        "Role Target",
        "role_target@test.com",
        "Test@123"
    )

    target_user = User.query.filter_by(
        email="role_target@test.com"
    ).first()

    assert target_user is not None

    response = client.patch(
        f"/api/admin/users/{target_user.id}/role",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "role": "agent"
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["message"] == "User role updated successfully"
    assert data["user"]["role"] == "agent"


def test_admin_can_change_user_status(client):
    admin_token = register_and_login(
        client,
        "Status Admin",
        "status_admin@test.com",
        "Test@123"
    )

    make_admin("status_admin@test.com")

    register_and_login(
        client,
        "Status Target",
        "status_target@test.com",
        "Test@123"
    )

    target_user = User.query.filter_by(
        email="status_target@test.com"
    ).first()

    assert target_user is not None

    response = client.patch(
        f"/api/admin/users/{target_user.id}/status",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "is_active": False
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["message"] == "User deactivated successfully"
    assert data["user"]["is_active"] is False


def test_admin_can_list_agents(client):
    admin_token = register_and_login(
        client,
        "Agent List Admin",
        "agent_list_admin@test.com",
        "Test@123"
    )

    make_admin("agent_list_admin@test.com")

    register_and_login(
        client,
        "Test Agent",
        "list_agent@test.com",
        "Test@123"
    )

    make_agent("list_agent@test.com")

    response = client.get(
        "/api/admin/agents",
        headers={
            "Authorization": f"Bearer {admin_token}"
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert "count" in data
    assert "agents" in data
    assert data["count"] >= 1


def test_admin_can_assign_ticket(client):
    admin_token = register_and_login(
        client,
        "Assignment Admin",
        "assignment_admin@test.com",
        "Test@123"
    )

    make_admin("assignment_admin@test.com")

    customer_token = register_and_login(
        client,
        "Assignment Customer",
        "assignment_customer@test.com",
        "Test@123"
    )

    register_and_login(
        client,
        "Assignment Agent",
        "assignment_agent@test.com",
        "Test@123"
    )

    make_agent("assignment_agent@test.com")

    agent = User.query.filter_by(
        email="assignment_agent@test.com"
    ).first()

    assert agent is not None

    ticket_id = create_ticket(
        client,
        customer_token
    )

    response = client.patch(
        f"/api/admin/tickets/{ticket_id}/assign",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "agent_id": agent.id
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["message"] == "Ticket assigned successfully"
    assert data["ticket"]["agent_id"] == agent.id
    assert data["ticket"]["status"] == "ASSIGNED"


def test_admin_stats(client):
    admin_token = register_and_login(
        client,
        "Stats Admin",
        "stats_admin@test.com",
        "Test@123"
    )

    make_admin("stats_admin@test.com")

    response = client.get(
        "/api/admin/stats",
        headers={
            "Authorization": f"Bearer {admin_token}"
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert "users" in data
    assert "tickets" in data
    assert "priorities" in data

    assert data["users"]["admins"] >= 1


def test_admin_requires_authentication(client):
    response = client.get("/api/admin/users")

    assert response.status_code == 401