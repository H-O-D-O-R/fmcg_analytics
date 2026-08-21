import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent

sys.path.append(
    str(ROOT_DIR)
)

from connection import Database


def load_schema():

    schema_path = (
        Path(__file__).resolve()
        .parent
        / "schema.sql"
    )

    with open(
        schema_path,
        "r",
        encoding="utf-8",
    ) as file:
        return file.read()



def initialize_database():

    db = Database()

    schema = load_schema()

    with db.connection() as connection:

        with connection.cursor() as cursor:

            cursor.execute(schema)


    print(
        "Database initialized successfully"
    )



if __name__ == "__main__":

    initialize_database()