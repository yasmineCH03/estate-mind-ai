from pydantic import BaseModel, Field
from typing import Optional, List


class RawListing(BaseModel):
    """Pydantic schema for LLM-extracted listing data.
    The LLM MUST return data matching this schema."""

    title: Optional[str] = Field(None, description="Title of the listing")
    property_type: Optional[str] = Field(
        None,
        description="One of: apartment, house, villa, studio, land, commercial"
    )
    transaction_type: Optional[str] = Field(
        None,
        description="One of: rent, sale"
    )
    price: Optional[float] = Field(None, description="Price as a number, no currency symbol")
    currency: str = Field("TND", description="Currency code")
    rooms: Optional[int] = Field(None, description="Number of rooms (S+2 = 2 rooms)")
    bedrooms: Optional[int] = Field(None, description="Number of bedrooms")
    bathrooms: Optional[int] = Field(None, description="Number of bathrooms")
    area_m2: Optional[float] = Field(None, description="Surface area in square meters")
    floor: Optional[int] = Field(None, description="Floor number")
    address: Optional[str] = Field(None, description="Full address")
    city: Optional[str] = Field(None, description="City name")
    delegation: Optional[str] = Field(None, description="Delegation / district")
    governorate: Optional[str] = Field(
        None,
        description="Tunisian governorate: Tunis, Ariana, Ben Arous, Manouba, Nabeul, "
                    "Zaghouan, Bizerte, Béja, Jendouba, Le Kef, Siliana, Sousse, Monastir, "
                    "Mahdia, Sfax, Kairouan, Kasserine, Sidi Bouzid, Gabès, Médenine, "
                    "Tataouine, Gafsa, Tozeur, Kébili"
    )
    features: List[str] = Field(
        default_factory=list,
        description="List of features: parking, elevator, garden, pool, furnished, "
                    "balcony, terrace, security, air_conditioning, central_heating, sea_view"
    )
    description: Optional[str] = Field(None, description="Cleaned description summary")
    standing: Optional[str] = Field(
        None,
        description="Standing/quality level: low, medium, high, luxury"
    )
    equipment: List[str] = Field(
        default_factory=list,
        description="Equipment: equipped_kitchen, central_heating, air_conditioning, etc."
    )