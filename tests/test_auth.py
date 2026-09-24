def test_register_success(client):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Test Customer",
            "email": "customer@test.com",
            "password": "Test@123"
        }
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["message"] == "User registered successfully"
    assert data["user"]["email"] == "customer@test.com"
    assert data["user"]["role"] == "customer"


def test_register_duplicate_email(client):
    payload = {
        "name": "Test Customer",
        "email": "duplicate@test.com",
        "password": "Test@123"
    }

    first_response = client.post(
        "/api/auth/register",
        json=payload
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/auth/register",
        json=payload
    )

    assert second_response.status_code == 409

    data = second_response.get_json()

    assert data["error"] == "Email already registered"


def test_login_success(client):
    client.post(
        "/api/auth/register",
        json={
            "name": "Login User",
            "email": "login@test.com",
            "password": "Test@123"
        }
    )

    response = client.post(
        "/api/auth/login",
        json={
            "email": "login@test.com",
            "password": "Test@123"
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["message"] == "Login successful"
    assert "access_token" in data
    assert data["user"]["email"] == "login@test.com"


def test_login_wrong_password(client):
    client.post(
        "/api/auth/register",
        json={
            "name": "Wrong Password User",
            "email": "wrong@test.com",
            "password": "Test@123"
        }
    )

    response = client.post(
        "/api/auth/login",
        json={
            "email": "wrong@test.com",
            "password": "WrongPassword"
        }
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["error"] == "Invalid email or password"


def test_me_requires_authentication(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_me_with_valid_token(client):
    client.post(
        "/api/auth/register",
        json={
            "name": "Me User",
            "email": "me@test.com",
            "password": "Test@123"
        }
    )

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "me@test.com",
            "password": "Test@123"
        }
    )

    login_data = login_response.get_json()
    token = login_data["access_token"]

    response = client.get(
        "/api/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["user"]["email"] == "me@test.com"
