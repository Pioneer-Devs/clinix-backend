import logging
from datetime import datetime

import httpx
from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.patient import Patient
from app.schemas.patient import PatientCreate

logger = logging.getLogger(__name__)


async def provision_solid_pod(patient_id, patient_name):
    # SOLID_SERVER_URL: where to TCP-connect (http://solid:3000 inside Docker)
    # SOLID_BASE_URL:   public-facing URL used by Solid as its baseUrl (http://localhost:3000)
    solid_server_url = settings.SOLID_SERVER_URL.rstrip("/")
    solid_base_url = getattr(settings, "SOLID_BASE_URL", solid_server_url).rstrip("/")
    # Extract just the host[:port] for the Host header
    solid_base_host = solid_base_url.split("//", 1)[-1].split("/")[0]

    slug = f"patient-{patient_id}"
    email = f"{slug}@clinix-pod.local"
    password = f"clinix-{patient_id}"

    try:
        async with httpx.AsyncClient(
            timeout=20,
            headers={"Host": solid_base_host},
        ) as client:
            # Step 1 — Get the controls (available endpoints)
            controls_res = await client.get(f"{solid_server_url}/.account/")
            controls_res.raise_for_status()
            controls = controls_res.json().get("controls", {})

            def get_internal_url(url):
                # Replace the public baseUrl (localhost:3000) with the internal server URL (solid:3000)
                if url and url.startswith(solid_base_url):
                    return url.replace(solid_base_url, solid_server_url, 1)
                return url

            create_url = get_internal_url(controls["account"]["create"])
            # Step 2 — Create account shell
            account_res = await client.post(
                create_url,
                json={}
            )
            if account_res.status_code not in (200, 201):
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Solid Account creation failed: {account_res.text}"
                )

            authorization = account_res.json().get("authorization")
            auth_header = {"authorization": f"CSS-Account-Token {authorization}", "Host": solid_base_host}

            # Step 3 — Get updated controls now that we're logged in
            auth_controls_res = await client.get(
                f"{solid_server_url}/.account/",
                headers=auth_header
            )
            auth_controls_res.raise_for_status()
            auth_controls = auth_controls_res.json().get("controls", {})

            password_create_url = get_internal_url(auth_controls.get("password", {}).get("create"))
            pod_url = get_internal_url(auth_controls["account"]["pod"])
            client_credentials_url = get_internal_url(auth_controls["account"]["clientCredentials"])

            # Step 4 — Register email/password login method
            if not password_create_url:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Solid Login method registration endpoint not found in auth_controls"
                )

            login_res = await client.post(
                password_create_url,
                headers=auth_header,
                json={"email": email, "password": password, "confirmPassword": password}
            )
            if login_res.status_code not in (200, 201):
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Solid Login method registration failed: {login_res.text}"
                )

            # Step 5 — Create the POD
            pod_res = await client.post(
                pod_url,
                headers=auth_header,
                json={"name": slug}
            )
            if pod_res.status_code not in (200, 201):
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Solid POD creation failed: {pod_res.text}"
                )

            # Step 5 — Create client credentials token
            token_res = await client.post(
                client_credentials_url,
                headers=auth_header,
                json={
                    "name": f"clinix-token-{patient_id}",
                    "webId": f"{solid_base_url}/{slug}/profile/card#me"
                }
            )
            if token_res.status_code not in (200, 201):
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Solid Token creation failed: {token_res.text}"
                )

            token_data = token_res.json()

    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Solid POD provisioning service HTTP error: {str(exc)}",
        ) from exc

    return {
        "solid_pod_url": f"{solid_base_url}/{slug}/",
        "solid_web_id": f"{solid_base_url}/{slug}/profile/card#me",
        "solid_token_id": token_data.get("id", token_data.get("token_id")),
        "solid_token_secret": token_data.get("secret", token_data.get("token_secret"))
    }


async def _provision_and_update(patient_id: str, patient_name: str):
    """Background task: provision Solid POD and persist the result.

    Runs after the patient has already been saved to the DB.
    Failures are logged but do not affect the patient record.
    """
    from app.core.database import SessionLocal  # local import to avoid circular deps

    try:
        solid_data = await provision_solid_pod(patient_id, patient_name)
    except Exception as exc:
        import traceback
        logger.error(
            "Solid POD provisioning FAILED for patient %s\nError: %s\nTraceback:\n%s",
            patient_id,
            exc,
            traceback.format_exc(),
        )
        print(f"\n❌ SOLID PROVISION ERROR for patient {patient_id}: {exc}", flush=True)
        print(traceback.format_exc(), flush=True)
        return

    # Open a fresh session for the background update
    session = SessionLocal()
    try:
        patient = session.get(Patient, patient_id)
        if patient:
            patient.solid_pod_url = solid_data["solid_pod_url"]
            patient.solid_web_id = solid_data["solid_web_id"]
            patient.solid_token_id = solid_data["solid_token_id"]
            patient.solid_token_secret = solid_data["solid_token_secret"]
            session.commit()
            logger.info("Solid POD provisioned for patient %s", patient_id)
            print(f"\n✅ SUCCESS: Solid POD perfectly provisioned for patient {patient_id}!", flush=True)
            print(f"POD URL: {solid_data['solid_pod_url']}\n", flush=True)
    finally:
        session.close()


async def create_patient(db: Session, payload: PatientCreate, background_tasks: BackgroundTasks) -> Patient:
    """Create a patient record immediately, then provision a Solid POD in the background.

    Patient creation succeeds even if the Solid server is unreachable.
    """
    patient = Patient(**payload.model_dump(), updated_at=datetime.utcnow())
    db.add(patient)
    try:
        db.commit()
        db.refresh(patient)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A patient with this hospital_id already exists.",
        ) from exc

    # Kick off Solid provisioning without blocking the response
    background_tasks.add_task(_provision_and_update, str(patient.id), patient.full_name)

    return patient


def search_patients(db: Session, query_text: str = "", limit: int = 20) -> list[Patient]:
    query = db.query(Patient)
    if query_text:
        like = f"%{query_text}%"
        query = query.filter(
            or_(
                Patient.hospital_id.ilike(like),
                Patient.first_name.ilike(like),
                Patient.last_name.ilike(like),
                Patient.phone.ilike(like),
            )
        )
    return query.order_by(Patient.created_at.desc()).limit(limit).all()


def get_patient_or_404(db: Session, patient_id) -> Patient:
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient
