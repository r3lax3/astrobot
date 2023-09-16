import asyncio
import logging
import sqlite3
import argparse


from src import main as bot_main


def run_sql_script(filename: str):
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()

        with open(filename, 'r') as f:
            sql_script = f.read()

        cursor.executescript(sql_script)
        conn.commit()

        logging.info('База успешно создана, все таблицы загружены.')


def parse_args():
    parser = argparse.ArgumentParser(description="My SQL script runner")
    parser.add_argument("--create_tables", action='store_true', help="Run the create tables script")
    parser.add_argument(
        "--update_interpretations",
        action='store_true',
        help="Update interpretations from ./interpretation.csv to database.db"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(level=0)

    if args.create_tables:
        logging.info("Обнаружен параметр create_tables. Начинаю процесс создания таблиц в базе данных")
        run_sql_script('database/scripts/create_tables.sql')

    if args.update_interpretations:
        logging.info("Обнаружен параметр update_interpretations. Начинаю процесс обновления интерпретаций")
        # update_interpretations()

    asyncio.run(bot_main())


if __name__ == '__main__':
    main()
