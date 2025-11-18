"""
Database Schemas for Food Waste App

Each Pydantic model represents a collection in MongoDB. The collection name is the
lowercase of the class name (e.g., Offer -> "offer").
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class User(BaseModel):
    name: str = Field(..., description="Full name")
    phone: Optional[str] = Field(None, description="Phone number for contact and pickup")
    email: Optional[str] = Field(None, description="Email address")
    is_active: bool = Field(True, description="Whether user is active")


class Store(BaseModel):
    name: str = Field(..., description="Store name")
    logo_url: Optional[str] = Field(None, description="Logo URL")
    address: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    lat: Optional[float] = Field(None, description="Latitude")
    lng: Optional[float] = Field(None, description="Longitude")
    cuisines: List[str] = Field(default_factory=list, description="Cuisine tags, e.g., bakery, sushi")


class Offer(BaseModel):
    store_id: str = Field(..., description="ID of the store offering the bag")
    title: str = Field(..., description="Short title for the surprise bag")
    description: Optional[str] = Field(None, description="Details about what could be inside")
    image_url: Optional[str] = Field(None, description="Representative image")
    city: str = Field(..., description="City for filtering")
    original_price: float = Field(..., ge=0, description="Original value of items")
    price: float = Field(..., ge=0, description="Discounted price for the bag")
    quantity: int = Field(..., ge=0, description="How many bags are available")
    pickup_start: datetime = Field(..., description="Pickup window start time (UTC)")
    pickup_end: datetime = Field(..., description="Pickup window end time (UTC)")
    tags: List[str] = Field(default_factory=list, description="Dietary or category tags")


class Reservation(BaseModel):
    offer_id: str = Field(..., description="Reserved offer ID")
    user_name: str = Field(..., description="Name for pickup")
    user_phone: str = Field(..., description="Contact phone number")
    status: str = Field("reserved", description="Reservation status: reserved, picked_up, cancelled")
    pickup_code: Optional[str] = Field(None, description="Code shown at pickup for verification")
