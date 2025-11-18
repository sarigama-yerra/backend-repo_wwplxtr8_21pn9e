import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents

app = FastAPI(title="Food Waste Saver API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OfferCreate(BaseModel):
    store_id: str
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    city: str
    original_price: float
    price: float
    quantity: int
    pickup_start: datetime
    pickup_end: datetime
    tags: List[str] = []


class ReservationCreate(BaseModel):
    offer_id: str
    user_name: str
    user_phone: str


@app.get("/")
def read_root():
    return {"message": "Food Waste Saver Backend is running"}


@app.get("/offers")
def list_offers(city: Optional[str] = None, tag: Optional[str] = None):
    """List active offers, optionally filtered by city and tag"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    filter_dict = {}
    now = datetime.utcnow()
    filter_dict["pickup_end"] = {"$gte": now}
    filter_dict["quantity"] = {"$gt": 0}

    if city:
        filter_dict["city"] = {"$regex": f"^{city}$", "$options": "i"}
    if tag:
        filter_dict["tags"] = tag

    offers = get_documents("offer", filter_dict)

    # Transform ObjectId and datetime for JSON
    def serialize(doc):
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        for k, v in list(doc.items()):
            if isinstance(v, datetime):
                doc[k] = v.isoformat()
        return doc

    return [serialize(o) for o in offers]


@app.post("/offers", status_code=201)
def create_offer(payload: OfferCreate):
    """Create a new offer"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    offer_id = create_document("offer", payload.model_dump())
    return {"id": offer_id}


@app.post("/reservations", status_code=201)
def create_reservation(payload: ReservationCreate):
    """Reserve a bag, decrementing available quantity atomically"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    # Atomically decrement quantity if > 0
    res = db["offer"].find_one_and_update(
        {"_id": ObjectId(payload.offer_id), "quantity": {"$gt": 0}},
        {"$inc": {"quantity": -1}, "$set": {"updated_at": datetime.utcnow()}},
        return_document=True,
    )
    if not res:
        raise HTTPException(status_code=400, detail="Offer sold out or not found")

    reservation = {
        "offer_id": payload.offer_id,
        "user_name": payload.user_name,
        "user_phone": payload.user_phone,
        "status": "reserved",
        "pickup_code": str(ObjectId())[-6:].upper(),
    }
    reservation_id = create_document("reservation", reservation)
    return {"id": reservation_id, "pickup_code": reservation["pickup_code"]}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
