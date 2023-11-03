from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    name = Column(String)
    role = Column(String)
    birth_datetime = Column(String)
    birth_location_id = Column(Integer, ForeignKey('locations.id'))
    current_location_id = Column(Integer, ForeignKey('locations.id'))
    every_day_prediction_time = Column(String)
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

    id = Column(Integer, primary_key=True)
    type = Column(String)
    longitude = Column(Float)
    latitude = Column(Float)
    title = Column(String)


class Interpretation(Base):
    __tablename__ = 'interpretations'

    id = Column(Integer, primary_key=True)
    natal_planet = Column(String)
    transit_planet = Column(String)
    aspect = Column(String)
    interpretation = Column(String)


class GeneralPrediction(Base):
    __tablename__ = 'general_predictions'
    
    date = Column(String, primary_key=True)
    prediction = Column(String)


class ViewedPrediction(Base):
    __tablename__ = 'viewed_predictions'
    
    user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    prediction_date = Column(String, primary_key=True)
    view_timestamp = Column(DateTime, default=func.current_timestamp())
    
    user = relationship("User", back_populates="viewed_predictions")

    
class CardOfDay(Base):
    __tablename__ = 'cards_of_day'
    
    message_id = Column(Integer, primary_key=True)


# @dataclass
# class MandatorySubChannel:
#     channel_id: int
#     title: str
#     invite_link: str
