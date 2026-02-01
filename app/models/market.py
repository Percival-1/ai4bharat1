"""
Market data models for price information and market intelligence.
"""

from datetime import date
from typing import Optional

from sqlalchemy import DECIMAL, Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class MarketPrice(Base):
    """Market price model for storing mandi price information."""

    __tablename__ = "market_prices"

    # Market information
    mandi_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Crop information
    crop_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Price information
    price_per_quintal: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)

    # Date information
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Location information
    location_lat: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 8), nullable=True)
    location_lng: Mapped[Optional[float]] = mapped_column(DECIMAL(11, 8), nullable=True)
    location_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    district: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # Additional market data
    quality_grade: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Market metadata
    source: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # Source of the price data

    # Price trends
    previous_price: Mapped[Optional[float]] = mapped_column(
        DECIMAL(10, 2), nullable=True
    )
    price_change_percentage: Mapped[Optional[float]] = mapped_column(
        DECIMAL(5, 2), nullable=True
    )

    def __repr__(self) -> str:
        """String representation of the market price."""
        return f"<MarketPrice(id={self.id}, mandi={self.mandi_name}, crop={self.crop_name}, price={self.price_per_quintal}, date={self.date})>"
