from sqlalchemy import (
    Column, 
    Integer,
    String, 
    Float, 
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    name = Column(String)
    role = Column(String)
    birth_datetime = Column(String)  # "%d.%m.%Y %H:%M" as default
    birth_location_id = Column(
        Integer, 
        ForeignKey('locations.id')
    )
    current_location_id = Column(
        Integer, 
        ForeignKey('locations.id')
    )
    every_day_prediction_time = Column(String)  # "%H:%M" as default
    subscription_end_date = Column(String)
    gender = Column(String)
    timezone_offset = Column(Integer)
    last_card_update = Column(String)
    card_message_id = Column(Integer)

    birth_location = relationship(
        "Location", 
        foreign_keys=[birth_location_id]
    )
    current_location = relationship(
        "Location", 
        foreign_keys=[current_location_id]
    )


class Location(Base):
    __tablename__ = 'locations'

    id: int = Column(Integer, primary_key=True)
    type: str = Column(String)
    longitude: float = Column(Float)
    latitude: float = Column(Float)
    title: str = Column(String)


class Interpretation(Base):
    __tablename__ = 'interpretations'

    id: int = Column(Integer, primary_key=True)
    natal_planet: str = Column(String)
    transit_planet: str = Column(String)
    aspect: str = Column(String)
    interpretation: str = Column(String)


class GeneralPrediction(Base):
    __tablename__ = 'general_predictions'
    
    date: str = Column(String, primary_key=True)
    prediction: str = Column(String)


class ViewedPrediction(Base):
    __tablename__ = 'viewed_predictions'
    
    user_id: int = Column(
        Integer, 
        ForeignKey('users.user_id'),
        primary_key=True
    )
    prediction_date: str = Column(
        String, 
        primary_key=True
    )
    view_timestamp: str = Column(String)  # "%d.%m.%Y" as default
    

class CardOfDay(Base):
    __tablename__ = 'cards_of_day'
    
    message_id: str = Column(Integer, primary_key=True)


class Payment(Base):
    __tablename__ = 'payments'

    payment_id: str = Column(String, primary_key=True)
    user_id: int = Column(Integer, ForeignKey('users.user_id'))
    status: str = Column(String)  # 'success' | 'failed' | 'pending'
    period: int = Column(Integer)
    created_at: str = Column(String)  # "%d.%m.%Y %H:%M" as default
    ended_at: str = Column(String)  # "%d.%m.%Y %H:%M" as default

