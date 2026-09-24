from app.extensions import db
from app.models.user import User


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


def create_agent(app, name="Test Agent", email="agent@test.com"):
    with app.app_context():
        agent = User(
            name=name,
            email=email,
            role="agent"
        )
        agent.set_password("Test@123")

        db.session.add(agent)
        db.session.commit()

        return agent.id


def test_assign_ticket_to_agent(client, app):
    customer_token = register_and_login(
        client,
        "Assignment Customer",
        "assignment@test.com"
    )

    agent_id = create_agent(app)

    create_response = client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "title": "Assignment test",
            "description": "Testing ticket assignment"
        }
    )

    ticket_id = create_response.get_json()["ticket"]["id"]

    agent_token = register_and_login(
        client,
        "Admin User",
        "admin@test.com"
    )

    with app.app_context():
        user = User.query.filter_by(email="admin@test.com").first()
        user.role = "admin"
        db.session.commit()

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@test.com",
            "password": "Test@123"
        }
    )

    agent_token = login_response.get_json()["access_token"]

    response = client.patch(
        f"/api/tickets/{ticket_id}/assign",
        headers={"Authorization": f"Bearer {agent_token}"},
        json={
            "agent_id": agent_id
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["message"] == "Ticket assigned successfully"


def test_assign_invalid_agent(client, app):
    customer_token = register_and_login(
        client,
        "Invalid Agent Customer",
        "invalidagent@test.com"
    )

    create_response = client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "title": "Invalid agent test",
            "description": "Testing invalid agent"
        }
    )

    ticket_id = create_response.get_json()["ticket"]["id"]

    admin_token = register_and_login(
        client,
        "Admin Invalid Agent",
        "admininvalid@test.com"
    )

    with app.app_context():
        user = User.query.filter_by(email="admininvalid@test.com").first()
        user.role = "admin"
        db.session.commit()

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "admininvalid@test.com",
            "password": "Test@123"
        }
    )

    admin_token = login_response.get_json()["access_token"]

    response = client.patch(
        f"/api/tickets/{ticket_id}/assign",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "agent_id": 99999
        }
    )

    assert response.status_code == 404

    data = response.get_json()

    assert data["error"] == "Agent not found"


def test_agent_updates_ticket_status(client, app):
    customer_token = register_and_login(
        client,
        "Status Customer",
        "statuscustomer@test.com"
    )

    agent_id = create_agent(
        app,
        "Status Agent",
        "statusagent@test.com"
    )

    create_response = client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "title": "Status test",
            "description": "Testing status update"
        }
    )

    ticket_id = create_response.get_json()["ticket"]["id"]

    with app.app_context():
        agent = db.session.get(User, agent_id)
        agent_email = agent.email

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": agent_email,
            "password": "Test@123"
        }
    )

    agent_token = login_response.get_json()["access_token"]

    admin_token = register_and_login(
        client,
        "Status Admin",
        "statusadmin@test.com"
    )

    with app.app_context():
        admin = User.query.filter_by(email="statusadmin@test.com").first()
        admin.role = "admin"
        db.session.commit()

    admin_login = client.post(
        "/api/auth/login",
        json={
            "email": "statusadmin@test.com",
            "password": "Test@123"
        }
    )

    admin_token = admin_login.get_json()["access_token"]

    client.patch(
        f"/api/tickets/{ticket_id}/assign",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "agent_id": agent_id
        }
    )

    response = client.patch(
        f"/api/tickets/{ticket_id}/status",
        headers={"Authorization": f"Bearer {agent_token}"},
        json={
            "status": "IN_PROGRESS"
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["message"] == "Ticket status updated successfully"


def test_agent_cannot_update_unassigned_ticket(client, app):
    customer_token = register_and_login(
        client,
        "Unauthorized Status Customer",
        "unauthstatus@test.com"
    )

    agent_id = create_agent(
        app,
        "Unauthorized Agent",
        "unauthagent@test.com"
    )

    create_response = client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "title": "Unauthorized status",
            "description": "Testing unauthorized status update"
        }
    )

    ticket_id = create_response.get_json()["ticket"]["id"]

    with app.app_context():
        agent = db.session.get(User, agent_id)
        agent_email = agent.email

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": agent_email,
            "password": "Test@123"
        }
    )

    agent_token = login_response.get_json()["access_token"]

    response = client.patch(
        f"/api/tickets/{ticket_id}/status",
        headers={"Authorization": f"Bearer {agent_token}"},
        json={
            "status": "IN_PROGRESS"
        }
    )

    assert response.status_code == 403


def test_customer_can_add_comment(client):
    token = register_and_login(
        client,
        "Comment Customer",
        "commentcustomer@test.com"
    )

    create_response = client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Comment test",
            "description": "Testing comments"
        }
    )

    ticket_id = create_response.get_json()["ticket"]["id"]

    response = client.post(
        f"/api/tickets/{ticket_id}/comments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "message": "Here is additional information"
        }
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["message"] == "Comment added successfully"


def test_customer_can_get_comments(client):
    token = register_and_login(
        client,
        "Get Comment Customer",
        "getcomment@test.com"
    )

    create_response = client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Get comments",
            "description": "Testing comment retrieval"
        }
    )

    ticket_id = create_response.get_json()["ticket"]["id"]

    client.post(
        f"/api/tickets/{ticket_id}/comments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "message": "First comment"
        }
    )

    response = client.get(
        f"/api/tickets/{ticket_id}/comments",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200

    data = response.get_json()

    assert len(data["comments"]) == 1
    assert data["comments"][0]["message"] == "First comment"


def test_comment_requires_message(client):
    token = register_and_login(
        client,
        "Empty Comment Customer",
        "emptycomment@test.com"
    )

    create_response = client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Empty comment",
            "description": "Testing empty comment"
        }
    )

    ticket_id = create_response.get_json()["ticket"]["id"]

    response = client.post(
        f"/api/tickets/{ticket_id}/comments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "message": "   "
        }
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "message is required"