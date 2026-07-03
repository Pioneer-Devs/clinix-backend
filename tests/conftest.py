import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db, engine
from app.models.user import User
from app.models.enums import UserRole
from app.utils.auth import hash_password

@pytest.fixture(scope="function")
def setup_database():
    """Ensure a clean database for each test by dropping and recreating all tables."""
    from sqlmodel import SQLModel
    import app.models  # load models to register them on SQLModel metadata
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)



@pytest.fixture(scope="function")
def db_session(setup_database):
    """
    Creates a new database session with a rollback mechanism to ensure
    tests don't affect the actual database state.
    """
    connection = engine.connect()
    transaction = connection.begin()
    
    # bind an individual Session to the connection
    session = Session(bind=connection)
    
    # start a SAVEPOINT
    session.begin_nested()
    
    # Each time a SAVEPOINT ends, start a new one
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        if transaction.nested and not transaction._parent.nested:
            session.begin_nested()
            
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_student(db_session):
    user = User(
        email="student@test.com",
        password_hash=hash_password("password123"),
        first_name="Test",
        last_name="Student",
        role=UserRole.student,
        year_of_study=4,
        matric_number="MAT123",
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture(scope="function")
def test_supervisor(db_session):
    user = User(
        email="supervisor@test.com",
        password_hash=hash_password("password123"),
        first_name="Test",
        last_name="Supervisor",
        role=UserRole.supervisor,
        hospital="LUTH",
        mdcn_reg_no="MDCN123",
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture(scope="function")
def test_patient(db_session):
    from app.models.patient import Patient
    from app.models.enums import Gender
    from datetime import date
    patient = Patient(
        first_name="John",
        last_name="Doe",
        gender=Gender.male,
        date_of_birth=date(1990, 1, 1),
        hospital_id="HOSP123",
        phone="08012345678",
        created_by_id=None
    )
    db_session.add(patient)
    db_session.commit()
    return patient

@pytest.fixture(scope="function")
def student_auth_headers(client, test_student):
    response = client.post("/api/v1/auth/login", data={"username": test_student.email, "password": "password123"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def supervisor_auth_headers(client, test_supervisor):
    response = client.post("/api/v1/auth/login", data={"username": test_supervisor.email, "password": "password123"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
