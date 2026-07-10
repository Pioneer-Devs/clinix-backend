import base64
import hashlib
import json
from datetime import datetime, timedelta
from urllib.parse import urlparse, quote
from uuid import uuid4

import httpx
import jwt
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import HTTPException, status

from app.core.config import settings
from app.models.enums import WalletRecordStatus
from app.models.wallet import WalletRecord


CLINIX = "https://clinix.ng/vocab#"
SCHEMA = "https://schema.org/"


def create_wallet_record_for_encounter(db, encounter, patient):
    existing = (
        db.query(WalletRecord)
        .filter(WalletRecord.encounter_id == encounter.id)
        .first()
    )
    if existing:
        return existing

    wallet_record = WalletRecord(
        patient_id=patient.id,
        encounter_id=encounter.id,
        qr_payload=f"CLINIX-ENC-{encounter.id}-{datetime.utcnow().date().isoformat()}",
        solid_pod_url=None,
        status=WalletRecordStatus.pending,
    )
    db.add(wallet_record)
    return wallet_record


def get_latest_patient_wallet_record(db, patient_id):
    return (
        db.query(WalletRecord)
        .filter(WalletRecord.patient_id == patient_id)
        .order_by(WalletRecord.created_at.desc())
        .first()
    )


def get_patient_wallet_qr(db, patient_id):
    wallet_record = get_latest_patient_wallet_record(db, patient_id)
    if not wallet_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No wallet record exists for this patient")
    return build_wallet_qr_response(wallet_record)


def build_wallet_qr_response(wallet_record):
    encounter = wallet_record.encounter
    patient = wallet_record.patient
    if not encounter or not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet record is missing encounter or patient data")

    if not patient.solid_pod_url or not patient.solid_web_id or not patient.solid_token_id or not patient.solid_token_secret:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Patient Solid POD credentials are not provisioned")

    access_url = f"/wallet/view?pod={patient.solid_pod_url}&enc={encounter.id}"

    return {
        "qr_payload": wallet_record.qr_payload,
        "access_url": access_url,
        "expires_at": datetime.utcnow() + timedelta(days=1),
        "encounter": {
            "encounter_id": encounter.id,
            "patient_id": patient.id,
            "patient_name": patient.full_name,
            "solid_pod_url": patient.solid_pod_url,
            "solid_web_id": patient.solid_web_id,
            "solid_token_id": patient.solid_token_id,
            "solid_token_secret": patient.solid_token_secret,
            "chief_complaint": encounter.chief_complaint,
            "diagnosis": encounter.working_diagnosis,
            "ai_diagnosis": encounter.ai_diagnosis,
            "ai_confidence": encounter.ai_confidence,
            "treatment_plan": encounter.treatment_plan,
            "follow_up": encounter.follow_up,
            "vitals": encounter.vitals or {},
            "finalized_at": encounter.finalized_at,
            "associated_symptoms": encounter.associated_symptoms or [],
            "investigations": encounter.investigations or [],
            "wallet_status": wallet_record.status,
        },
    }


def confirm_solid_push(db, patient_id, solid_pod_url):
    wallet_record = get_latest_patient_wallet_record(db, patient_id)
    if not wallet_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No wallet record exists for this patient")

    wallet_record.solid_pod_url = solid_pod_url
    wallet_record.status = WalletRecordStatus.pushed
    wallet_record.pushed_at = datetime.utcnow()
    db.add(wallet_record)
    db.commit()
    db.refresh(wallet_record)
    return wallet_record


async def push_patient_wallet_to_pod(db, patient_id):
    wallet_record = get_latest_patient_wallet_record(db, patient_id)
    if not wallet_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No wallet record exists for this patient")

    encounter = wallet_record.encounter
    patient = wallet_record.patient
    if not encounter or not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet record is missing encounter or patient data")

    if not patient.solid_pod_url or not patient.solid_token_id or not patient.solid_token_secret:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Patient Solid POD credentials are not provisioned")

    if wallet_record.status == WalletRecordStatus.pushed and wallet_record.solid_pod_url:
        pod_url_encoded = quote(wallet_record.solid_pod_url, safe="")
        return {
            "qr_url": f"{settings.FRONTEND_URL}/wallet/view?pod={pod_url_encoded}&enc={str(encounter.id)}",
            "solid_pod_url": wallet_record.solid_pod_url,
        }

    key = ec.generate_private_key(ec.SECP256R1())
    token_url = _join_url(settings.SOLID_SERVER_URL, ".oidc/token")
    token_proof_url = _solid_public_url(token_url)

    base_headers = _solid_base_headers()
    async with httpx.AsyncClient(timeout=20.0, headers=base_headers) as client:
        access_token = await _fetch_solid_access_token(client, token_url, token_proof_url, patient, key)
        dataset_url = _join_url(patient.solid_pod_url, "clinix/encounters", str(encounter.id))
        dataset_request_url = _solid_request_url(dataset_url)

        await _ensure_solid_container(client, _join_url(patient.solid_pod_url, "clinix/"), access_token, key)
        await _ensure_solid_container(client, _join_url(patient.solid_pod_url, "clinix/encounters/"), access_token, key)
        await _put_encounter_turtle(client, dataset_url, dataset_request_url, access_token, key, encounter, patient)
        await _put_encounter_acl(client, dataset_url, access_token, key, patient.solid_web_id)

    wallet_record.solid_pod_url = patient.solid_pod_url
    wallet_record.status = WalletRecordStatus.pushed
    wallet_record.pushed_at = datetime.utcnow()
    db.add(wallet_record)
    db.commit()
    db.refresh(wallet_record)

    pod_url_encoded = quote(patient.solid_pod_url, safe="")
    qr_url = f"{settings.FRONTEND_URL}/wallet/view?pod={pod_url_encoded}&enc={encounter.id}"
    return {
        "qr_url": qr_url,
        "solid_pod_url": patient.solid_pod_url,
    }


async def _fetch_solid_access_token(client, token_url, token_proof_url, patient, key):
    headers = {
        "DPoP": _build_dpop_proof("POST", token_proof_url, key),
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "client_credentials",
        "scope": "webid",
    }

    try:
        response = await client.post(
            token_url,
            data=data,
            headers=headers,
            auth=(patient.solid_token_id, patient.solid_token_secret),
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Unable to reach the Solid token endpoint") from exc

    if response.status_code >= 400:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Solid token exchange failed: {response.text}")

    token_data = response.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Solid token endpoint did not return an access token")
    return access_token


async def _ensure_solid_container(client, container_url, access_token, key):
    request_url = _solid_request_url(container_url)
    headers = _solid_auth_headers("PUT", container_url, access_token, key)
    headers.update({
        "Content-Type": "text/turtle",
        "Link": '<http://www.w3.org/ns/ldp#BasicContainer>; rel="type"',
    })

    response = await client.put(request_url, content="", headers=headers)
    if response.status_code in {200, 201, 204, 409, 412}:
        return
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Solid container write failed: {response.text}")


async def _put_encounter_turtle(client, dataset_url, dataset_request_url, access_token, key, encounter, patient):
    headers = _solid_auth_headers("PUT", dataset_url, access_token, key)
    headers.update({
        "Content-Type": "text/turtle",
        "Link": '<http://www.w3.org/ns/ldp#Resource>; rel="type"',
    })

    response = await client.put(dataset_request_url, content=_encounter_to_turtle(dataset_url, encounter, patient), headers=headers)
    if response.status_code not in {200, 201, 204}:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Solid encounter write failed: {response.text}")


async def _put_encounter_acl(client, dataset_url, access_token, key, solid_web_id):
    acl_url = f"{dataset_url}.acl"
    acl_request_url = _solid_request_url(acl_url)
    headers = _solid_auth_headers("PUT", acl_url, access_token, key)
    headers.update({
        "Content-Type": "text/turtle",
    })

    acl_content = f"""@prefix acl: <http://www.w3.org/ns/auth/acl#> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .

<#public>
    a acl:Authorization ;
    acl:agentClass foaf:Agent ;
    acl:accessTo <{dataset_url}> ;
    acl:mode acl:Read .

<#owner>
    a acl:Authorization ;
    acl:agent <{solid_web_id}> ;
    acl:accessTo <{dataset_url}> ;
    acl:mode acl:Read, acl:Write, acl:Control .
"""

    response = await client.put(acl_request_url, content=acl_content.encode(), headers=headers)
    if response.status_code not in {200, 201, 204}:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Solid ACL write failed: {response.text}")


def _solid_auth_headers(method, url, access_token, key):
    return {
        "Authorization": f"DPoP {access_token}",
        "DPoP": _build_dpop_proof(method, url, key, access_token),
    }


def _build_dpop_proof(method, url, key, access_token=None):
    now = int(datetime.utcnow().timestamp())
    claims = {
        "htu": url,
        "htm": method.upper(),
        "iat": now,
        "jti": str(uuid4()),
    }
    if access_token:
        claims["ath"] = _base64url(hashlib.sha256(access_token.encode("utf-8")).digest())

    return jwt.encode(
        claims,
        key,
        algorithm="ES256",
        headers={
            "typ": "dpop+jwt",
            "jwk": _public_jwk(key),
        },
    )


def _public_jwk(key):
    public_numbers = key.public_key().public_numbers()
    return {
        "kty": "EC",
        "crv": "P-256",
        "x": _base64url(public_numbers.x.to_bytes(32, "big")),
        "y": _base64url(public_numbers.y.to_bytes(32, "big")),
    }


def _base64url(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _encounter_to_turtle(dataset_url, encounter, patient):
    subject = f"<{dataset_url}#encounter>"
    finalized_at = encounter.finalized_at.isoformat() if encounter.finalized_at else ""
    vitals = json.dumps(encounter.vitals or {}, default=str)
    symptoms = json.dumps(encounter.associated_symptoms or [], default=str)
    investigations = json.dumps(encounter.investigations or [], default=str)

    triples = [
        "@prefix clinix: <https://clinix.ng/vocab#> .",
        "@prefix schema: <https://schema.org/> .",
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
        "",
        f"{subject}",
        "    a clinix:Encounter ;",
        f"    schema:identifier {_literal(str(encounter.id))} ;",
        f"    schema:patient {_literal(patient.full_name)} ;",
        f"    clinix:encounter_id {_literal(str(encounter.id))} ;",
        f"    clinix:patient_id {_literal(str(patient.id))} ;",
        f"    clinix:chief_complaint {_literal(encounter.chief_complaint or '')} ;",
        f"    clinix:diagnosis {_literal(encounter.working_diagnosis or '')} ;",
        f"    clinix:ai_diagnosis {_literal(encounter.ai_diagnosis or '')} ;",
        f"    clinix:treatment_plan {_literal(encounter.treatment_plan or '')} ;",
        f"    clinix:follow_up {_literal(encounter.follow_up or '')} ;",
        f"    clinix:vitals {_literal(vitals)} ;",
        f"    clinix:associated_symptoms {_literal(symptoms)} ;",
        f"    clinix:investigations {_literal(investigations)} ;",
        f"    clinix:solid_web_id {_literal(patient.solid_web_id or '')} ;",
    ]

    if encounter.ai_confidence is not None:
        triples.append(f"    clinix:ai_confidence {encounter.ai_confidence} ;")
    if finalized_at:
        triples.append(f"    clinix:finalized_at {_literal(finalized_at)}^^xsd:dateTime ;")
        triples.append(f"    schema:dateCreated {_literal(finalized_at)}^^xsd:dateTime ;")

    triples[-1] = triples[-1].rstrip(" ;") + " ."
    return "\n".join(triples) + "\n"


def _literal(value):
    return json.dumps(value)


def _join_url(*parts):
    cleaned = []
    trailing_slash = False
    for index, part in enumerate(parts):
        text = str(part or "")
        if index == len(parts) - 1 and text.endswith("/"):
            trailing_slash = True
        text = text.strip("/")
        if text:
            cleaned.append(text)

    if not cleaned:
        return "/"

    first = cleaned[0]
    if "://" in first:
        scheme, rest = first.split("://", 1)
        url = f"{scheme}://{rest.strip('/')}"
        if len(cleaned) > 1:
            url = f"{url}/{'/'.join(cleaned[1:])}"
    else:
        url = "/".join(cleaned)

    if trailing_slash and not url.endswith("/"):
        url = f"{url}/"
    return url


def _solid_base_headers():
    solid_base_url = getattr(settings, "SOLID_BASE_URL", None)
    if not solid_base_url:
        return {}

    solid_base_host = solid_base_url.rstrip("/").split("//", 1)[-1].split("/")[0]
    return {"Host": solid_base_host}


def _solid_request_url(url):
    solid_base_url = getattr(settings, "SOLID_BASE_URL", None)
    solid_server_url = settings.SOLID_SERVER_URL.rstrip("/")
    if solid_base_url and url.startswith(solid_base_url.rstrip("/")):
        return url.replace(solid_base_url.rstrip("/"), solid_server_url, 1)
    return url


def _solid_public_url(url):
    solid_base_url = getattr(settings, "SOLID_BASE_URL", None)
    solid_server_url = settings.SOLID_SERVER_URL.rstrip("/")
    if solid_base_url and url.startswith(solid_server_url):
        return url.replace(solid_server_url, solid_base_url.rstrip("/"), 1)
    return url


def _pod_slug(pod_url):
    path_parts = [part for part in urlparse(pod_url).path.split("/") if part]
    if not path_parts:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Patient Solid POD URL does not include a POD slug")
    return path_parts[0]
