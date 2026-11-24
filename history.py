import json
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Any


DATABASE_PATH = Path(__file__).with_name("calculadora_numerica.db")


def initialize_database(database_path: Path = DATABASE_PATH) -> None:
    with closing(sqlite3.connect(database_path)) as connection:
        with connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    method TEXT NOT NULL,
                    expression TEXT NOT NULL,
                    parameters_json TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    description TEXT NOT NULL
                )
                """
            )


def create_operation(
    method: str,
    expression: str,
    parameters: dict[str, int | float],
    result: dict[str, float | int],
    description: str,
    database_path: Path = DATABASE_PATH,
) -> int:
    with closing(sqlite3.connect(database_path)) as connection:
        with connection:
            cursor = connection.execute(
                """
                INSERT INTO operations
                    (created_at, method, expression, parameters_json, result_json, description)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().astimezone().isoformat(timespec="seconds"),
                    method,
                    expression,
                    json.dumps(parameters),
                    json.dumps(result),
                    description,
                ),
            )
            return int(cursor.lastrowid)


def get_operations(database_path: Path = DATABASE_PATH) -> list[dict[str, Any]]:
    with closing(sqlite3.connect(database_path)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT * FROM operations ORDER BY id DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def update_description(
    operation_id: int,
    description: str,
    database_path: Path = DATABASE_PATH,
) -> None:
    with closing(sqlite3.connect(database_path)) as connection:
        with connection:
            cursor = connection.execute(
                "UPDATE operations SET description = ? WHERE id = ?",
                (description, operation_id),
            )
            if cursor.rowcount == 0:
                raise ValueError("No se encontró el cálculo que intentas editar.")


def delete_operation(operation_id: int, database_path: Path = DATABASE_PATH) -> None:
    with closing(sqlite3.connect(database_path)) as connection:
        with connection:
            cursor = connection.execute(
                "DELETE FROM operations WHERE id = ?", (operation_id,)
            )
            if cursor.rowcount == 0:
                raise ValueError("No se encontró el cálculo que intentas eliminar.")
