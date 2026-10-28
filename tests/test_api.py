"""Small automated tests. Run from backend/: pytest -q

SQLite is used for these API tests so a running PostgreSQL server is not needed.
The actual project uses PostgreSQL.
"""
import os
os.environ["JWT_SECRET"] = "unit-test-secret-please-never-use-in-production-1234567890"
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["GEMINI_API_KEY"] = ""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.models import User
from app.security import hash_password
import app.main as main_module


def make_client():
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(bind=engine)
    with testing_session() as db:
        db.add_all([
            User(name="Admin", email="admin@test.local", password_hash=hash_password("testingpass123"), role="admin", department="IT"),
            User(name="Doctor", email="doctor@test.local", password_hash=hash_password("testingpass123"), role="doctor", department="Medicine"),
            User(name="Reception", email="reception@test.local", password_hash=hash_password("testingpass123"), role="receptionist", department="Reception"),
        ])
        db.commit()

    def override_db():
        with testing_session() as db:
            yield db

    main_module.app.dependency_overrides[get_db] = override_db
    return TestClient(main_module.app), engine


def login(client, email):
    r = client.post("/api/auth/login", data={"username": email, "password": "testingpass123"})
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["access_token"]}


def test_login_and_permissions():
    client, engine = make_client()
    with client:
        assert client.get("/api/patients").status_code == 401
        assert client.post("/api/auth/login", data={"username": "admin@test.local", "password": "wrong"}).status_code == 401
        doc = login(client, "doctor@test.local")
        assert client.post("/api/auth/staff", headers=doc, json={"name":"Someone","email":"some@test.local","password":"123456789","role":"admin"}).status_code == 403
        receptionist = login(client, "reception@test.local")
        patient = client.post("/api/patients", headers=receptionist, json={
            "full_name":"Fake Test Patient","date_of_birth":"1993-03-12","sex":"Female",
            "phone":"0000000000","address":"fictional","blood_group":"O+"})
        assert patient.status_code == 201, patient.text
        patient_id = patient.json()["id"]
        assert client.get("/api/patients", headers=doc).json()[0]["id"] == patient_id
        assert client.post("/api/visits", headers=receptionist, json={"patient_id":patient_id,"doctor_id":2}).status_code == 403
        assert client.post("/api/visits", headers=doc, json={"patient_id":patient_id,"doctor_id":2,"notes":"Fake note"}).status_code == 201
        bill = client.post("/api/bills", headers=receptionist, json={"patient_id":patient_id,"description":"Training exam","amount":"200.00"})
        assert bill.status_code == 201, bill.text
        bill_id = bill.json()["id"]
        assert client.post(f"/api/bills/{bill_id}/payments", headers=receptionist, json={"amount":"250.00","method":"cash"}).status_code == 400
        assert client.post(f"/api/bills/{bill_id}/payments", headers=receptionist, json={"amount":"50.00","method":"upi"}).status_code == 200
        assert client.get("/api/bills", headers=doc).status_code == 403
        ai = client.post("/api/ai/operations-advice", headers=receptionist, json={
            "question":"How can we reduce clinic queue times without extra staff?", "confirm_no_patient_data":True})
        assert ai.status_code == 503  # intentionally no Gemini key configured
    client.app.dependency_overrides.clear()
    engine.dispose()


def test_inventory_and_beds():
    client, engine = make_client()
    with client:
        admin = login(client, "admin@test.local")
        item = client.post("/api/inventory", headers=admin, json={
            "name":"Training masks", "sku":"TST-1", "quantity":3, "reorder_level":5, "unit_price":"10.00"})
        assert item.status_code == 201, item.text
        item_id = item.json()["id"]
        assert client.patch(f"/api/inventory/{item_id}/stock", headers=admin, json={"change":-4}).status_code == 400
        assert client.patch(f"/api/inventory/{item_id}/stock", headers=admin, json={"change":10}).json()["quantity"] == 13
        bed = client.post("/api/beds", headers=admin, json={"ward":"Sample ward","bed_number":"S-1"})
        assert bed.status_code == 201
        assert client.post("/api/beds", headers=admin, json={"ward":"Sample ward","bed_number":"S-1"}).status_code == 409
    client.app.dependency_overrides.clear()
    engine.dispose()
