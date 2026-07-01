def test_create_patient(client, student_auth_headers):
    response = client.post("/api/v1/patients", headers=student_auth_headers, json={
        "first_name": "Alice",
        "last_name": "Smith",
        "gender": "F",
        "date_of_birth": "1995-05-15",
        "hospital_id": "ALICE123",
        "phone": "08098765432"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "Alice"
    assert data["hospital_id"] == "ALICE123"

def test_search_patients(client, student_auth_headers, test_patient):
    response = client.get(f"/api/v1/patients/search?q={test_patient.first_name}", headers=student_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["first_name"] == test_patient.first_name

def test_get_patient(client, student_auth_headers, test_patient):
    response = client.get(f"/api/v1/patients/{test_patient.id}", headers=student_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_patient.id)
    assert data["first_name"] == test_patient.first_name
