from app.models.enums import EncounterStatus

def test_create_encounter(client, student_auth_headers, test_patient):
    response = client.post("/api/v1/encounters", headers=student_auth_headers, json={
        "patient_id": str(test_patient.id),
        "chief_complaint": "Headache and fever",
        "notes": "Patient complains of severe headache for 3 days."
    })
    assert response.status_code == 201
    data = response.json()
    assert data["chief_complaint"] == "Headache and fever"
    assert data["status"] == EncounterStatus.draft.value

def test_list_encounters(client, student_auth_headers):
    response = client.get("/api/v1/encounters", headers=student_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_finalize_encounter(client, student_auth_headers, test_patient):
    # First create an encounter
    response = client.post("/api/v1/encounters", headers=student_auth_headers, json={
        "patient_id": str(test_patient.id),
        "chief_complaint": "Stomach ache",
    })
    encounter_id = response.json()["id"]

    # Add required fields before finalizing
    client.patch(f"/api/v1/encounters/{encounter_id}", headers=student_auth_headers, json={
        "working_diagnosis": "Gastritis",
        "treatment_plan": "Antacids and rest"
    })

    # Now finalize it
    response = client.post(f"/api/v1/encounters/{encounter_id}/finalize", headers=student_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == EncounterStatus.pending_review.value

def test_approve_encounter(client, supervisor_auth_headers, student_auth_headers, test_patient, test_supervisor):
    # Student creates
    resp1 = client.post("/api/v1/encounters", headers=student_auth_headers, json={
        "patient_id": str(test_patient.id),
        "chief_complaint": "Cough",
    })
    enc_id = resp1.json()["id"]
    
    # Update required fields
    client.patch(f"/api/v1/encounters/{enc_id}", headers=student_auth_headers, json={
        "working_diagnosis": "Viral URI",
        "treatment_plan": "Fluids and rest"
    })
    
    # Finalize
    client.post(f"/api/v1/encounters/{enc_id}/finalize", headers=student_auth_headers)

    # Supervisor approves
    resp2 = client.post(f"/api/v1/encounters/{enc_id}/approve", headers=supervisor_auth_headers, json={
        "feedback": "Good job",
        "awarded_points": 10
    })
    assert resp2.status_code == 200
    assert resp2.json()["status"] == EncounterStatus.finalized.value
