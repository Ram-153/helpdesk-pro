import io


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


def create_ticket(client, token):
    response = client.post(
        "/api/tickets",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "title": "Attachment Test Ticket",
            "description": "Testing ticket attachments",
            "category": "Technical",
            "priority": "MEDIUM"
        }
    )

    assert response.status_code == 201

    return response.get_json()["ticket"]["id"]


def test_attachment_upload_and_list(client):
    token = register_and_login(
        client,
        "Attachment Customer",
        "attachment_customer@test.com",
        "Test@123"
    )

    ticket_id = create_ticket(client, token)

    response = client.post(
        f"/api/tickets/{ticket_id}/attachments",
        headers={
            "Authorization": f"Bearer {token}"
        },
        data={
            "file": (
                io.BytesIO(b"Hello HelpDesk Pro"),
                "test.txt"
            )
        },
        content_type="multipart/form-data"
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data is not None
    assert "attachment" in data

    list_response = client.get(
        f"/api/tickets/{ticket_id}/attachments",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert list_response.status_code == 200

    list_data = list_response.get_json()

    assert "attachments" in list_data
    assert len(list_data["attachments"]) == 1


def test_attachment_requires_authentication(client):
    response = client.get(
        "/api/tickets/1/attachments"
    )

    assert response.status_code == 401


def test_attachment_access_denied_for_other_customer(client):
    customer1_token = register_and_login(
        client,
        "Customer One",
        "customer_one_attachment@test.com",
        "Test@123"
    )

    customer2_token = register_and_login(
        client,
        "Customer Two",
        "customer_two_attachment@test.com",
        "Test@123"
    )

    ticket_id = create_ticket(client, customer1_token)

    response = client.get(
        f"/api/tickets/{ticket_id}/attachments",
        headers={
            "Authorization": f"Bearer {customer2_token}"
        }
    )

    assert response.status_code == 403


def test_attachment_upload_requires_file(client):
    token = register_and_login(
        client,
        "No File Customer",
        "no_file_attachment@test.com",
        "Test@123"
    )

    ticket_id = create_ticket(client, token)

    response = client.post(
        f"/api/tickets/{ticket_id}/attachments",
        headers={
            "Authorization": f"Bearer {token}"
        },
        data={},
        content_type="multipart/form-data"
    )

    assert response.status_code == 400


def test_attachment_download(client):
    token = register_and_login(
        client,
        "Download Customer",
        "download_attachment@test.com",
        "Test@123"
    )

    ticket_id = create_ticket(client, token)

    upload_response = client.post(
        f"/api/tickets/{ticket_id}/attachments",
        headers={
            "Authorization": f"Bearer {token}"
        },
        data={
            "file": (
                io.BytesIO(b"Download test content"),
                "download-test.txt"
            )
        },
        content_type="multipart/form-data"
    )

    assert upload_response.status_code == 201

    attachment_id = upload_response.get_json()["attachment"]["id"]

    download_response = client.get(
        f"/api/attachments/{attachment_id}",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert download_response.status_code == 200
    assert download_response.data == b"Download test content"
