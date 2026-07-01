def test_register_student_success(client):
    response = client.post("/api/v1/auth/register", json={
        "email": "newstudent@test.com",
        "password": "password123",
        "first_name": "New",
        "last_name": "Student",
        "role": "student",
        "year_of_study": 3,
        "matric_number": "MAT999"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newstudent@test.com"
    assert data["role"] == "student"
    assert data["is_verified"] is False

def test_register_duplicate_email(client, test_student):
    response = client.post("/api/v1/auth/register", json={
        "email": test_student.email,
        "password": "password123",
        "first_name": "Duplicate",
        "last_name": "User",
        "role": "student",
        "year_of_study": 3,
        "matric_number": "MAT998"
    })
    assert response.status_code == 409

def test_login_success(client, test_student):
    response = client.post("/api/v1/auth/login", data={
        "username": test_student.email,
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

def test_login_invalid_password(client, test_student):
    response = client.post("/api/v1/auth/login", data={
        "username": test_student.email,
        "password": "wrongpassword"
    })
    assert response.status_code == 401

def test_get_me_unauthorized(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401

def test_get_me_authorized(client, student_auth_headers, test_student):
    response = client.get("/api/v1/auth/me", headers=student_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_student.email
