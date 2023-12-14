import logging

from datetime import timedelta, datetime
from typing import Optional, List

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from src import config
from src.utils import get_timezone_offset
from src.database.models import (
    Base,
    Promocode,
    User,
    Location, 
    Interpretation,
    CardOfDay,
    Payment,
    ViewedPrediction,
    GeneralPrediction
)


DATETIME_FORMAT: str = config.get('database.datetime_format')
DATE_FORMAT: str = config.get('database.date_format')


class Database:
    def __init__(self):
        # Initialize the engine
        self.engine = create_engine('sqlite:///database.db')

        # Create tables in the database
        Base.metadata.create_all(self.engine)

        # Create a session
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def add_user(self, user: User):
        try:
            self.session.add(user)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()

    def get_users(self):
        return self.session.query(User).all()

    def get_user(self, user_id: int) -> User:
        return self.session.query(User).filter_by(user_id=user_id).first()

    def update_user_every_day_prediction_time(
        self, 
        user_id: int,
        hour: int, 
        minute: int
    ):
        user = self.session.query(
            User
        ).filter_by(
            user_id=user_id
        ).first()
        if user:
            user.every_day_prediction_time = "{:02d}:{:02d}".format(
                hour, 
                minute
            )
            self.session.commit()


    def update_user_current_location(
        self, 
        user_id: int, 
        new_location: Location
    ):
        user = self.session.query(
            User
        ).filter_by(
            user_id=user_id
        ).first()
        if user:
            old_location_id = user.current_location_id

            # Добавляем новое местоположение и получаем его ID
            new_location_id = self.add_location(new_location)

            # Обновляем ID текущего местоположения пользователя
            user.current_location_id = new_location_id

            # Удаляем старое местоположение
            old_location = self.session.query(
                Location
            ).filter_by(
                id=old_location_id
            ).first()
            if old_location:
                self.session.delete(old_location)

            self.session.commit()
        else:
            logging.info(f"User with ID {user_id} not found.")


    def update_user_card_of_day(
        self, 
        user_id: int, 
        card_message_id: int,
        card_update_time: str
    ):
        user = self.session.query(
            User
        ).filter_by(
            user_id=user_id
        ).first()
        if user:
            user.last_card_update = card_update_time
            user.card_message_id = card_message_id
            self.session.commit()

    def delete_user(self, user_id: int):
        user = self.session.query(
            User
        ).filter_by(
            user_id=user_id
        ).first()
        if user:
            self.session.delete(user)
            self.session.commit()

    def add_period_to_subscription_end_date(
        self,
        user_id: int,
        period: timedelta
    ):
        user = self.session.query(
            User
        ).filter_by(
            user_id=user_id
        ).first()
        if user:
            current_location = self.session.query(
                Location
            ).filter_by(
                id=user.current_location_id
            ).first()
            if current_location:
                time_offset = get_timezone_offset(
                    current_location.latitude, 
                    current_location.longitude
                )
                now = datetime.utcnow() + timedelta(hours=time_offset)
                current_user_subscription_end_date = datetime.strptime(
                    user.subscription_end_date,
                    DATETIME_FORMAT
                )
                start = max(
                    [
                        current_user_subscription_end_date,
                        now
                    ]
                )
                user.subscription_end_date = (start + period).strftime(
                    DATETIME_FORMAT
                )
                self.session.commit()

    def update_subscription_end_date(
        self, 
        user_id: int, 
        date: datetime
    ):
        user = self.session.query(
            User
        ).filter_by(
            user_id=user_id
        ).first()
        if user:
            current_location = self.session.query(
                Location
            ).filter_by(
                id=user.current_location_id
            ).first()
            if current_location:
                time_offset: int = get_timezone_offset(
                    current_location.latitude, 
                    current_location.longitude
                )
                new_subscription_end_date = date + timedelta(
                    hours=time_offset
                )
            user.subscription_end_date = new_subscription_end_date.strftime(
                    DATETIME_FORMAT
                )
            self.session.commit()

    
    def change_user_gender(
        self, 
        user_id: int,
        gender: str | None
    ):
        user = self.session.query(
            User
        ).filter_by(
            user_id=user_id
        ).first()
        if user:
            user.gender = gender
            self.session.commit()



    # Location table methods


    # Create
    def add_location(self, location: Location) -> int:
        """
        Метод используется для добавления локации в список.
        Тип может быть "birth" или "current".
        """
        self.session.add(location)
        self.session.commit()
        return location.id

    def get_location(self, location_id: int) -> Location:
        location = self.session.query(
            Location
        ).filter_by(
            id=location_id
        ).first()
        if location:
            return location
        raise Exception(
            'Чет локейшн в табличке с юзерами записан, а самой локации нет. '
            f'Айди - {location_id}'
        )


    def update_location(self, location: Location):
        existing_location = self.session.query(
            Location
        ).filter_by(
            id=location.id
        ).first()
        if existing_location:
            existing_location.longitude = location.longitude
            existing_location.latitude = location.latitude
            self.session.commit()

    def delete_location(self, location_id: int):
        location = self.session.query(
            Location
        ).filter_by(
            id=location_id
        ).first()
        if location:
            self.session.delete(location)
            self.session.commit()


    # Interpretations table methods

    def get_interpretation(
        self,
        natal_planet: str,
        transit_planet: str, 
        aspect: str
    ) -> Optional[str]:
        interpretation = self.session.query(
            Interpretation
        ).filter_by(
            natal_planet=natal_planet, 
            transit_planet=transit_planet, 
            aspect=aspect
        ).first()
        if interpretation:
            return interpretation.interpretation
        return None


    # Create
    def add_or_update_interpretation(
        self, 
        interpretation_obj: Interpretation
    ):
        existing_interpretation = self.session.query(
            Interpretation
        ).filter_by(
            natal_planet=interpretation_obj.natal_planet, 
            transit_planet=interpretation_obj.transit_planet, 
            aspect=interpretation_obj.aspect
        ).first()
        if existing_interpretation:
            existing_interpretation.interpretation = interpretation_obj.interpretation
        else:
            self.session.add(interpretation_obj)
        self.session.commit()


    # General Predictions

    def add_general_prediction(self, date: str, prediction: str):
        try:
            general_prediction = GeneralPrediction(
                date=date,
                prediction=prediction)
            self.session.add(general_prediction)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()

    def get_general_prediction(self, date: str) -> Optional[str]:
        prediction = self.session.query(
            GeneralPrediction
        ).filter_by(
            date=date
        ).first()
        return prediction.prediction if prediction else None

    def delete_general_prediction(self, date: str) -> Optional[str]:
        prediction = self.session.query(
            GeneralPrediction
        ).filter_by(
            date=date
        ).first()
        if prediction:
            self.session.delete(prediction)
            self.session.commit()
        else:
            raise Exception(
                f"Нет прогноза для указанной даты: {date}"
            )


    # Viewed Predictions

    # Create
    def add_viewed_prediction(
        self, 
        user_id: int, 
        prediction_date: str
    ):
        try:
            viewed_prediction = ViewedPrediction(
                user_id=user_id,
                prediction_date=prediction_date,
                view_timestamp=datetime.utcnow().strftime(
                    DATETIME_FORMAT
                )
            )
            self.session.add(viewed_prediction)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()


    # Read
    def get_viewed_predictions_by_user(
        self, 
        user_id: int
    ) -> list:
        predictions = self.session.query(
            ViewedPrediction
        ).filter_by(
            user_id=user_id
        ).all()
        return [
            (
                p.prediction_date,
                p.view_timestamp
            ) 
            for p in predictions
        ]

    def get_unviewed_predictions_count(
        self, 
        user_id: int
    ) -> int:
        # Получаем пользователя и его детали.
        user = self.session.query(
            User
        ).filter_by(
            user_id=user_id
        ).first()
        if not user:
            return 0  # Пользователь не найден.

        current_location = self.session.query(
            Location
        ).filter_by(
            id=user.current_location_id
        ).first()
        if not current_location:
            return 0  # Местоположение пользователя не найдено.

        # Вычисляем текущую дату с учетом часового пояса пользователя.
        time_offset: int = get_timezone_offset(
            current_location.latitude, 
            current_location.longitude
        )
        now = datetime.utcnow() + timedelta(hours=time_offset)

        # Проверяем, не истекла ли подписка.
        subscription_end_date = datetime.strptime(
            user.subscription_end_date,  # str
            DATETIME_FORMAT
        )
        if subscription_end_date < now:
            return 0  # Подписка истекла.

        # Вычисляем общее количество дней от текущей даты до окончания подписки.
        days_left = (subscription_end_date - now).days + 1  # "+1" чтобы включить начальную дату.

        # Получаем все даты прогнозов для данного пользователя.
        viewed_dates_strings = self.session.query(
            ViewedPrediction.prediction_date
        ).filter(
            ViewedPrediction.user_id == user_id
        ).all()

        # Преобразуем строки дат в объекты datetime.
        viewed_dates = [
            datetime.strptime(date[0], '%d.%m.%Y') 
            for date in viewed_dates_strings
        ]

        # Фильтруем даты, которые больше или равны текущей дате.
        viewed_dates_after_now = [
            date 
            for date in viewed_dates 
            if date >= now
        ]

        viewed_dates_count = len(viewed_dates_after_now)

        # Возвращаем количество непросмотренных прогнозов.
        unviewed_predictions = days_left - viewed_dates_count
        return max(0, unviewed_predictions)  # Убеждаемся, что результат неотрицательный.


    # Delete
    def delete_viewed_prediction(
        self, 
        user_id: int, 
        prediction_date: str
    ):
        prediction = self.session.query(
            ViewedPrediction
        ).filter_by(
            user_id=user_id, 
            prediction_date=prediction_date
        ).first()
        if prediction:
            self.session.delete(prediction)
            self.session.commit()
    
    # Cards of Day table methods

    # Create
    def add_card_of_day(self, message_id: int) -> None:
        card_of_day = CardOfDay(message_id=message_id)
        self.session.add(card_of_day)
        self.session.commit()

    def get_all_card_of_day(self) -> Optional[List[int]]:
        cards = self.session.query(
            CardOfDay
        ).all()
        return [card.message_id for card in cards]

    def delete_card_of_day(self, message_id: int) -> None:
        card_of_day = self.session.query(
            CardOfDay
        ).filter_by(
            message_id=message_id
        ).first()
        if card_of_day:
            self.session.delete(card_of_day)
            self.session.commit()

    # Payments
    def add_payment(self, payment: Payment):
        self.session.add(payment)
        self.session.commit()

    def update_payment(self, payment_id: int, **kwargs):
        payment = self.session.query(
            Payment
        ).filter_by(
            payment_id=payment_id
        ).first()
        if not payment:
            raise ValueError(f"No payment found with id {payment_id}")

        for key, value in kwargs.items():
            if hasattr(payment, key):
                setattr(payment, key, value)

        self.session.commit()

    def get_payments(self, **filters) -> List[Payment]:
        return self.session.query(
            Payment
        ).filter_by(
            **filters
        ).all()

    def get_promocode(self, promocode_str: str) -> Promocode:
        return self.session.query(Promocode).filter_by(promocode=promocode_str).first()
    
    def add_promocode(self, promocode_obj: Promocode):
        try:
            # Добавить объект Promocode в сессию
            self.session.add(promocode_obj)
            # Сохранить изменения
            self.session.commit()
        except IntegrityError:
            # Если произошла ошибка, откатить изменения
            self.session.rollback()
            raise

    def update_promocode(self, promocode_str: str, **kwargs):
        try:
            # Найти промокод в базе данных
            promocode = self.session.query(Promocode).filter_by(promocode=promocode_str).first()

            # Проверить, найден ли промокод
            if not promocode:
                raise ValueError("Промокод не найден")

            # Обновить поля промокода
            for key, value in kwargs.items():
                if hasattr(promocode, key):
                    setattr(promocode, key, value)
                else:
                    raise AttributeError(f"Атрибут '{key}' не существует в объекте Promocode")

            # Сохранить изменения
            self.session.commit()
        except Exception as e:
            # Если произошла ошибка, откатить изменения
            self.session.rollback()
            raise e

