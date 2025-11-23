from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from db import Base

class Pricing(Base):
    __tablename__ = "pricing"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True)  # ex: PB_price, lane_price, frais_prestation
    value = Column(Float)

class Club(Base):
    __tablename__ = "club"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    # stocker la configuration des jours et choix dans JSON string simple
    days_config = Column(String)  # exemple JSON: {"samedi":{"type":"PB","nb_lane":1}, ...}
    total_initial = Column(Float, default=0.0)
    total_paid = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    payments = relationship("Payment", back_populates="club")

    @property
    def remaining(self):
        return (self.total_initial or 0.0) - (self.total_paid or 0.0)

class Payment(Base):
    __tablename__ = "payment"
    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("club.id"))
    amount = Column(Float)
    note = Column(String, nullable=True)
    date = Column(DateTime, default=datetime.utcnow)

    club = relationship("Club", back_populates="payments")
