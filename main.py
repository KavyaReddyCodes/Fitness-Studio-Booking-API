from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import List, Optional
import pytz
import logging

app = FastAPI(title="Fitness Studio Booking API")

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("booking_api")

# In-memory DB
classes_db = [
    {
        "id": 1,
        "name": "Yoga",
        "instructor": "Aarti",
        "datetime": datetime(2025, 6, 25, 7, 0, tzinfo=pytz.timezone('Asia/Kolkata')),
        "available_slots": 5
    },
    {
        "id": 2,
        "name": "Zumba",
        "instructor": "Ravi",
        "datetime": datetime(2025, 6, 25, 18, 0, tzinfo=pytz.timezone('Asia/Kolkata')),
        "available_slots": 3
    },
    {
        "id": 3,
        "name": "HIIT",
        "instructor": "Sara",
        "datetime": datetime(2025, 6, 26, 6, 0, tzinfo=pytz.timezone('Asia/Kolkata')),
        "available_slots": 2
    }
]

bookings_db = []

class ClassResponse(BaseModel):
    id: int
    name: str
    instructor: str
    datetime: str  # ISO string in client's timezone
    available_slots: int

class BookingRequest(BaseModel):
    class_id: int = Field(..., gt=0)
    client_name: str = Field(..., min_length=1)
    client_email: EmailStr

class BookingResponse(BaseModel):
    class_id: int
    client_name: str
    client_email: EmailStr
    class_name: str
    class_time: str

@app.get("/classes", response_model=List[ClassResponse])
def get_classes(timezone: Optional[str] = Query("Asia/Kolkata", description="Client timezone e.g., 'UTC', 'Europe/London'")):
    try:
        client_tz = pytz.timezone(timezone)
    except pytz.UnknownTimeZoneError:
        raise HTTPException(status_code=400, detail="Invalid timezone")

    return [
        {
            **cls,
            "datetime": cls["datetime"].astimezone(client_tz).isoformat()
        }
        for cls in classes_db
    ]

@app.post("/book", response_model=BookingResponse)
def book_class(booking: BookingRequest):
    selected_class = next((cls for cls in classes_db if cls["id"] == booking.class_id), None)

    if not selected_class:
        raise HTTPException(status_code=404, detail="Class not found")

    if selected_class["available_slots"] <= 0:
        raise HTTPException(status_code=400, detail="No slots available")

    selected_class["available_slots"] -= 1
    new_booking = {
        "class_id": booking.class_id,
        "client_name": booking.client_name,
        "client_email": booking.client_email,
        "class_name": selected_class["name"],
        "class_time": selected_class["datetime"].isoformat()
    }
    bookings_db.append(new_booking)

    logger.info(f"New booking: {new_booking}")

    return new_booking

@app.get("/bookings", response_model=List[BookingResponse])
def get_bookings(email: EmailStr):
    user_bookings = [b for b in bookings_db if b["client_email"] == email]
    if not user_bookings:
        raise HTTPException(status_code=404, detail="No bookings found for this email")
    return user_bookings
