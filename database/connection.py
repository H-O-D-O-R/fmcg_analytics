from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor

from config import (
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_PORT,
)


class Database:

    def __init__(self):
        pass


    def connect(self):
        return psycopg2.connect(
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        )


    @contextmanager
    def connection(self):

        connection = self.connect()

        try:
            yield connection

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()


    def execute(
        self,
        query,
        params=None,
    ):

        with self.connection() as connection:

            with connection.cursor(
                cursor_factory=RealDictCursor
            ) as cursor:

                cursor.execute(
                    query,
                    params
                )

                return cursor.fetchall()


    def execute_one(
        self,
        query,
        params=None,
    ):

        with self.connection() as connection:

            with connection.cursor(
                cursor_factory=RealDictCursor
            ) as cursor:

                cursor.execute(
                    query,
                    params
                )

                return cursor.fetchone()


    def execute_script(
        self,
        script,
    ):

        with self.connection() as connection:

            with connection.cursor() as cursor:

                cursor.execute(
                    script
                )


def get_connection():

    db = Database()

    return db.connect()