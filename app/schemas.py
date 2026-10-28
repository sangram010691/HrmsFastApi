"""Request and response validation kept separate from database tables."""
from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class FromDB(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginIn(BaseModel):
    email: str
    password: str


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=8, max_length=128)
    role: Literal["admin", "receptionist", "doctor", "nurse", "lab"]
    department: str = Field(default="General", max_length=100)


class UserOut(FromDB):
    id: int
    name: str
    email: str
    role: str
    department: str
    active: bool


class PatientIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    date_of_birth: date
    sex: Literal["Female", "Male", "Other"]
    phone: str = Field(default="", max_length=30)
    address: str = Field(default="", max_length=2000)
    blood_group: str = Field(default="Unknown", max_length=10)

    @field_validator("date_of_birth")
    @classmethod
    def valid_dob(cls, value):
        if value > date.today():
            raise ValueError("Birth date cannot be in the future")
        return value


class PatientOut(PatientIn, FromDB):
    id: int
    created_at: datetime


class AppointmentIn(BaseModel):
    patient_id: int = Field(gt=0)
    doctor_id: int = Field(gt=0)
    scheduled_at: datetime
    reason: str = Field(default="", max_length=250)


class AppointmentStatus(BaseModel):
    status: Literal["scheduled", "completed", "cancelled"]


class AppointmentOut(AppointmentIn, FromDB):
    id: int
    status: str


class VisitIn(BaseModel):
    patient_id: int = Field(gt=0)
    doctor_id: int = Field(gt=0)
    diagnosis: str = Field(default="", max_length=5000)
    notes: str = Field(default="", max_length=10000)
    prescription: str = Field(default="", max_length=5000)


class VisitOut(VisitIn, FromDB):
    id: int
    created_at: datetime


class BillIn(BaseModel):
    patient_id: int = Field(gt=0)
    description: str = Field(min_length=2, max_length=250)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class BillOut(BillIn, FromDB):
    id: int
    paid_amount: Decimal
    created_at: datetime


class PaymentIn(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    method: Literal["cash", "card", "upi", "bank"]


class InventoryIn(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    sku: str = Field(min_length=2, max_length=70)
    quantity: int = Field(ge=0)
    reorder_level: int = Field(ge=0)
    unit_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class InventoryOut(InventoryIn, FromDB):
    id: int


class StockChange(BaseModel):
    change: int = Field(ge=-100000, le=100000)


class LabIn(BaseModel):
    patient_id: int = Field(gt=0)
    doctor_id: int = Field(gt=0)
    test_name: str = Field(min_length=2, max_length=180)


class LabOut(LabIn, FromDB):
    id: int
    status: str
    result: str


class LabResult(BaseModel):
    result: str = Field(min_length=1, max_length=5000)


class BedIn(BaseModel):
    ward: str = Field(min_length=2, max_length=80)
    bed_number: str = Field(min_length=1, max_length=25)


class BedOut(BedIn, FromDB):
    id: int
    patient_id: int | None


class BedAssignment(BaseModel):
    patient_id: int = Field(gt=0)


class AIRequest(BaseModel):
    question: str = Field(min_length=15, max_length=1500)
    confirm_no_patient_data: bool
