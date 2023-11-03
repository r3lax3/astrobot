import sqlite3
import logging

from datetime import timedelta, datetime

from typing import Optional, Any, List

from src import config
from src.utils import get_timezone_offset
from src.database.models import (
    User,
    Location, 
    Interpretation 
)


database_datetime_format: str = config.get(
    'database.datetime_format'
)
date_format: str = config.get(
    'database.date_format'
)



class Database:
    def __init__(self):
        self.connection = sqlite3.connect("database.db")
        self.cursor = self.connection.cursor()

    def execute_query(
        self,
        query: str,
        kwargs: dict = {},
        params: tuple = (),
        fetchone: bool = False,
        fetchall: bool = False,
    ) -> Any:
        if kwargs:
            keys = []
            kwargs_params = []

            for k, v in kwargs.items():
                keys.append(
                    f'{k} = ?'
                )
                kwargs_params.append(v)

            query += ' WHERE ' + ' AND '.join(keys)
            params = tuple(kwargs_params)

        # print(f'{query = }')
        # print(f'{params = }')

        self.cursor.execute(query, params)
        if fetchone:
            return self.cursor.fetchone()
        elif fetchall:
            return self.cursor.fetchall()
        else:
            self.connection.commit()

    # Users table methods


    # Create
    def add_user(
        self, 
        user_id: int, 
        name: str,
        role: str,
        birth_datetime, 
        birth_location: Location, 
        subscription_end_date: str,
        current_location: Optional[Location] = None,
        gender: Optional[str] = None,
        timezone_offset: Optional[int] = None,
        last_card_update: Optional[str] = None,
        card_id: Optional[int] = None
    ):
        # Add locations
        birth_location_id = self.add_location(birth_location)  # add and return id of row
        if current_location is not None:
            current_location_id = self.add_location(current_location)  # here too
        else:
            current_location_id = 0
        self.execute_query(
            query="""
            INSERT OR REPLACE INTO users (
                user_id,
                name,
                role, 
                birth_datetime, 
                birth_location_id, 
                current_location_id, 
                every_day_prediction_time,
                subscription_end_date,
                gender,
                timezone_offset,
                last_card_update,
                card_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            params=(
                user_id,
                name,
                role, 
                birth_datetime, 
                birth_location_id, 
                current_location_id, 
                "07:30", 
                subscription_end_date,
                gender,
                timezone_offset,
                last_card_update,
                card_id
            )
        )

    def get_user(self, user_id: int) -> User | None:
        query = """
        SELECT 
            user_id,
            name,
            role, 
            birth_datetime, 
            birth_location_id, 
            current_location_id, 
            every_day_prediction_time,
            subscription_end_date,
            gender,
            timezone_offset,
            last_card_update,
            card_id
        FROM users
        """
        result = self.execute_query(
            query, 
            kwargs={'user_id': user_id},
            fetchone=True
        )
        if result:
            return User(*result)

    def update_user_every_day_prediction_time(
        self, 
        user_id: int,
        hour: int, 
        minute: int
    ):
        query = '''
        UPDATE users 
        SET every_day_prediction_time = ? 
        WHERE user_id = ?
        '''

        time = "{:02d}:{:02d}".format(hour, minute)
        params = (time, user_id)

        self.execute_query(query, params=params)

    def update_user_current_location(
        self,
        user_id: int, 
        new_location: Location
    ):
        # 1. Get the current location id of the user
        user = self.get_user(user_id)
        if user is not None:
            old_location_id = user.current_location_id

            # 2. Insert the new location
            new_location_id = self.add_location(new_location)

            # 3. Update the user's current location id
            query = """
                UPDATE users 
                SET current_location_id=? 
                WHERE user_id=?
            """
            self.execute_query(
                query,
                params=(new_location_id, user_id)
            )

            # 4. Delete the old location from the locations table
            self.delete_location(old_location_id)
        else:
            logging.info(f"User with ID {user_id} not found.")

    def update_user_card_of_day(
        self,
        user_id: int,
        card_message_id: int,
        card_update_time: str
    ):
        query = '''
        UPDATE users
        SET last_card_update = ?, card_message_id = ?
        WHERE user_id = ?
        '''
        self.execute_query(
            query,
            params=(
                card_update_time, 
                card_message_id, 
                user_id
            )
        )


    def delete_user(self, user_id: int):
        query = "DELETE FROM users"
        self.execute_query(query, kwargs={'user_id': user_id})

    def add_period_to_subscription_end_date(
        self, 
        user_id: int, 
        period: timedelta
    ) -> None:
        user: User = self.get_user(user_id)
        current_location = self.get_location(
            user.current_location_id
        )
        time_offset: int = get_timezone_offset(
            current_location.latitude, 
            current_location.longitude
        )

        now = datetime.utcnow() + timedelta(hours=time_offset)
        current_user_subscription_end_date = datetime.strptime(
            user.subscription_end_date, database_datetime_format
        )
        start = max([current_user_subscription_end_date, now])
        
        query = "UPDATE users SET subscription_end_date = ?"
        self.execute_query(
            query=query,
            params=(
                (start + period).strftime(database_datetime_format),
            ),
            kwargs={'user_id': user_id}
        )

    def update_subscription_end_date(
        self, 
        user_id: int, 
        date: datetime
    ) -> None:
        user: User = self.get_user(user_id)
        current_location = self.get_location(
            user.current_location_id
        )

        time_offset: int = get_timezone_offset(
            current_location.latitude, 
            current_location.longitude
        )
        new_subscription_end_date = date + timedelta(hours=time_offset)

        query = '''
        UPDATE users 
        SET subscription_end_date = ? 
        WHERE user_id = ?
        '''
        self.execute_query(
            query=query,
            params=(
                new_subscription_end_date.strftime(
                    database_datetime_format
                ), 
                user_id
            )
        )
    
    def change_user_gender(
        self,
        gender: str | None,
        user_id: int
    ) -> None:
        query = '''
        UPDATE users 
        SET gender = ? 
        WHERE user_id = ?
        '''
        self.execute_query(
            query=query,
            params=(
                (gender, user_id)
            )
        )


    # Location table methods


    # Create
    def add_location(self, location: Location) -> int:
        """
        Метод используется для добавления локации в список
        тип может быть "birth" или "current"
        """
        self.execute_query(
            query="""
            INSERT INTO locations (
                type,
                longitude, 
                latitude
            )
            VALUES (?, ?, ?)
            """,
            params=(
                location.type,
                location.longitude,
                location.latitude
            )
        )
        
        location_id =  self.cursor.lastrowid
        if location_id is None:
            raise Exception(
                'Айдишник не возвращается, хотя должен. Ошибка в add_location'
            )
        else:
            return location_id

    def get_location(self, location_id: int) -> Location:
        query = """
        SELECT 
            id,
            type, 
            longitude, 
            latitude
        FROM locations
        """
        result = self.execute_query(
            query, 
            kwargs={'id': location_id}, 
            fetchone=True
        )
        if result:
            return Location(*result)
        raise Exception(
            'Чет локейшн в табличке с юзерами записан, а самой локации нет. '
            f'Айди - {location_id}'
        )

    def update_location(self, location: Location):
        query = """
        UPDATE locations 
        SET 
            longitude = ?, 
            latitude = ? 
        WHERE id=?
        """
        self.execute_query(
            query, 
            params=(
                location.longitude, 
                location.latitude, 
                location.id
            )
        )

    def delete_location(self, location_id: int):
        query = "DELETE FROM locations"
        self.execute_query(query, kwargs={'id': location_id})

    # Interpretations table methods

    def get_interpretation(
        self, 
        natal_planet: str,
        transit_planet: str,
        aspect: str
    ) -> Optional[str]:
        query = """
        SELECT interpretation
        FROM interpretations
        WHERE natal_planet = ? AND transit_planet = ? AND aspect = ?
        """
        result = self.execute_query(
            query, 
            params=(
                natal_planet, 
                transit_planet, 
                aspect
            ),
            fetchone=True
        )
        if result:
            return result[0]
        return None

    # Create
    def add_or_update_interpretation(
        self, 
        interpretation_obj: Interpretation
    ):
        query = """
        INSERT OR REPLACE INTO interpretations (
            natal_planet, 
            transit_planet,
            aspect, 
            interpretation
        )
        VALUES (?, ?, ?, ?)
        """
        self.execute_query(
            query,
            params=(
                interpretation_obj.natal_planet,
                interpretation_obj.transit_planet,
                interpretation_obj.aspect,
                interpretation_obj.interpretation
            )
        )

    # General Predictions

    # Create
    def add_general_prediction(
        self, 
        date: str,
        prediction: str
    ):
        query = """
            INSERT OR REPLACE INTO general_predictions (
                date, 
                prediction
            )
            VALUES (?, ?)
        """
        self.execute_query(
            query, 
            params=(date, prediction)
        )

    def get_general_prediction(self, date: str) -> Optional[str]:
        query = """
            SELECT prediction FROM general_predictions
        """
        result = self.execute_query(
            query, 
            kwargs={'date': date},
            fetchone=True
        )
        if result:
            return result[0]
        return None

    def delete_general_prediction(self, date: str):
        query = "DELETE FROM general_predictions"
        self.execute_query(query, kwargs={'date': date})


    # Viewed Predictions

    # Create
    def add_viewed_prediction(
        self, 
        user_id: int, 
        prediction_date: str
    ):
        query = """
        INSERT OR REPLACE INTO viewed_predictions (
            user_id, 
            prediction_date
        )
        VALUES (?, ?)
        """
        self.execute_query(
            query, 
            params=(user_id, prediction_date)
        )

    # Read
    def get_viewed_predictions_by_user(self, user_id: int) -> list:
        query = """
            SELECT prediction_date, view_timestamp 
            FROM viewed_predictions
        """
        return self.execute_query(
            query,
            kwargs={'user_id': user_id}, 
            fetchall=True
        )

    def get_unviewed_predictions_count(
        self,
        user_id: int
    ) -> int | None:
        # Get the user and their details.
        user = self.get_user(user_id)
        current_location = self.get_location(
            user.current_location_id
        )

        # Calculate the current date using the user's timezone.
        time_offset: int = get_timezone_offset(
            current_location.latitude, 
            current_location.longitude
        )
        now = datetime.utcnow() + timedelta(hours=time_offset)

        # Check if the subscription has already ended.
        subscription_end_date = datetime.strptime(
            user.subscription_end_date, 
            database_datetime_format
        )
        if subscription_end_date < now:
            return 0  # Subscription has ended.

        # Calculate the total number of days from now to the end of the subscription.
        days_left = (subscription_end_date - now).days + 1  # "+1" to include the start date.

        # Calculate how many days of predictions the user has already viewed, starting from today.
        viewed_dates_query = f"""
            SELECT prediction_date 
            FROM viewed_predictions 
            WHERE user_id = ?
            AND strftime(
                '%Y-%m-%d', 
                substr(prediction_date,7,4)||'-'||substr(prediction_date,4,2)||'-'||substr(prediction_date,1,2)
            ) >= ? 

        """
        viewed_dates = self.execute_query(
            viewed_dates_query, 
            params=(user_id, now.strftime('%Y-%m-%d')), fetchall=True
        )
        print(f'{viewed_dates}')
        viewed_dates_count = len(viewed_dates)

        # Return the number of unviewed predictions.
        unviewed_predictions = days_left - viewed_dates_count
         # Ensuring the result is non-negative.
        return max(0, unviewed_predictions) 

    # Delete
    def delete_viewed_prediction(
        self, 
        user_id: int,
        prediction_date: str
    ):
        query = """
        DELETE FROM viewed_predictions
        WHERE 
            user_id=? 
            AND 
            prediction_date=?
        """
        self.execute_query(
            query, 
            params=(user_id, prediction_date)
        )
    
    # Cards of Day table methods

    # Create
    def add_card_of_day(self, message_id: int) -> None:
        query = """
        INSERT INTO cards_of_day (
            message_id
        )
        VALUES (?)
        """
        self.execute_query(
            query,
            params=(message_id,)
        )

    def get_all_card_of_day(self) -> Optional[List[int]]:
        query = """
        SELECT message_id
        FROM cards_of_day
        """
        rows = self.execute_query(
            query, 
            fetchall=True
        )
        return [row[0] for row in rows]


    # Delete
    def delete_card_of_day(self, message_id: int) -> None:
        query = """
        DELETE FROM cards_of_day
        """
        self.execute_query(
            query, 
            kwargs={'message_id': message_id}
        )

        
    # MandatorySubChannel table methods

    # def add_mandatory_channel(self, channel: MandatorySubChannel):
    #     query = """
    #     INSERT INTO mandatory_sub_channels (channel_id, title, invite_link)
    #     VALUES (?, ?, ?)
    #     """
    #     self.execute_query(query, params=(channel.channel_id, channel.title, channel.invite_link))
    #
    # def get_mandatory_channel(self, channel_id: int) -> Optional[MandatorySubChannel]:
    #     query = "SELECT * FROM mandatory_sub_channels WHERE channel_id = ?"
    #     result = self.execute_query(query, params=(channel_id,), fetchone=True)
    #     if result:
    #         return MandatorySubChannel(*result)
    #     return None
    #
    # def update_mandatory_channel(self, channel: MandatorySubChannel):
    #     query = """
    #     UPDATE mandatory_sub_channels
    #     SET title = ?, invite_link = ?
    #     WHERE channel_id = ?
    #     """
    #     self.execute_query(query, params=(channel.title, channel.invite_link, channel.channel_id))
    #
    # def delete_mandatory_channel(self, channel_id: int):
    #     query = "DELETE FROM mandatory_sub_channels WHERE channel_id = ?"
    #     self.execute_query(query, params=(channel_id,))
