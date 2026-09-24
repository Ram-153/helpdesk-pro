from app.extensions import db
from app.models.user import User
from app.models.notification import Notification


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


def create_agent(app, name, email):
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


def test_get_notifications(client, app):
    token = register_and_login(
        client,
        "Notification User",
        "notification@test.com"
    )

    with app.app_context():
        user = User.query.filter_by(
            email="notification@test.com"
        ).first()

        notification = Notification(
            user_id=user.id,
            title="Test Notification",
            message="This is a test notification",
            notification_type="test"
        )

        db.session.add(notification)
        db.session.commit()

    response = client.get(
        "/api/notifications",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200

    data = response.get_json()

    assert "notifications" in data
    assert len(data["notifications"]) == 1
    assert data["notifications"][0]["title"] == "Test Notification"


def test_notification_requires_authentication(client):
    response = client.get("/api/notifications")

    assert response.status_code == 401


def test_mark_notification_as_read(client, app):
    token = register_and_login(
        client,
        "Read Notification User",
        "readnotification@test.com"
    )

    with app.app_context():
        user = User.query.filter_by(
            email="readnotification@test.com"
        ).first()

        notification = Notification(
            user_id=user.id,
            title="Unread Notification",
            message="Please read this",
            notification_type="test"
        )

        db.session.add(notification)
        db.session.commit()

        notification_id = notification.id

    response = client.patch(
        f"/api/notifications/{notification_id}/read",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200


def test_mark_all_notifications_as_read(client, app):
    token = register_and_login(
        client,
        "Read All User",
        "readall@test.com"
    )

    with app.app_context():
        user = User.query.filter_by(
            email="readall@test.com"
        ).first()

        for number in range(3):
            notification = Notification(
                user_id=user.id,
                title=f"Notification {number}",
                message=f"Message {number}",
                notification_type="test"
            )

            db.session.add(notification)

        db.session.commit()

    response = client.patch(
        "/api/notifications/read-all",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200


def test_ticket_creation_creates_agent_notification(client, app):
    agent_id = create_agent(
        app,
        "Notification Agent",
        "notificationagent@test.com"
    )

    customer_token = register_and_login(
        client,
        "Notification Customer",
        "notificationcustomer@test.com"
    )

    response = client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "title": "Notification ticket",
            "description": "Testing ticket notification"
        }
    )

    assert response.status_code == 201

    with app.app_context():
        notification = Notification.query.filter_by(
            user_id=agent_id,
            notification_type="ticket_created"
        ).first()

        assert notification is not None
        assert notification.title == "New Ticket Created"
        assert "Notification ticket" in notification.message


def test_status_update_creates_customer_notification(client, app):
    customer_token = register_and_login(
        client,
        "Status Notification Customer",
        "statusnotificationcustomer@test.com"
    )

    agent_id = create_agent(
        app,
        "Status Notification Agent",
        "statusnotificationagent@test.com"
    )

    create_response = client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "title": "Status notification ticket",
            "description": "Testing status notification"
        }
    )

    assert create_response.status_code == 201

    ticket_id = create_response.get_json()["ticket"]["id"]

    admin_token = register_and_login(
        client,
        "Notification Admin",
        "notificationadmin@test.com"
    )

    with app.app_context():
        admin = User.query.filter_by(
            email="notificationadmin@test.com"
        ).first()

        admin.role = "admin"
        db.session.commit()

    admin_login = client.post(
        "/api/auth/login",
        json={
            "email": "notificationadmin@test.com",
            "password": "Test@123"
        }
    )

    admin_token = admin_login.get_json()["access_token"]

    assign_response = client.patch(
        f"/api/tickets/{ticket_id}/assign",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "agent_id": agent_id
        }
    )

    assert assign_response.status_code == 200

    agent_login = client.post(
        "/api/auth/login",
        json={
            "email": "statusnotificationagent@test.com",
            "password": "Test@123"
        }
    )

    agent_token = agent_login.get_json()["access_token"]

    status_response = client.patch(
        f"/api/tickets/{ticket_id}/status",
        headers={"Authorization": f"Bearer {agent_token}"},
        json={
            "status": "IN_PROGRESS"
        }
    )

    assert status_response.status_code == 200

    with app.app_context():
        customer = User.query.filter_by(
            email="statusnotificationcustomer@test.com"
        ).first()

        notification = Notification.query.filter_by(
            user_id=customer.id,
            notification_type="ticket_status_updated"
        ).first()

        assert notification is not None
        assert notification.title == "Ticket Status Updated"
