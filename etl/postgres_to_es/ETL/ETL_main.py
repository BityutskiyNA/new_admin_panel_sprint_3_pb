import sqlite3
import time

import psycopg2
from psycopg2.extras import DictCursor
from contextlib import contextmanager
from functools import wraps
import elasticsearch

from ETL_Extract import Pg_extractor, SQLiteExtractor
from ETL_Load import Loader
from ETL_Models import Movie_PD, Param
from ETL_settings import Settings_BS
from loging_my import logger_one

setings_bs = Settings_BS()


@contextmanager
def open_db(file_name: str):
    conn = sqlite3.connect(file_name)
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()


@contextmanager
def open_pg(dsl: dict):
    conn = psycopg2.connect(**dsl, cursor_factory=DictCursor)
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()


def download_data_film(record_status: SQLiteExtractor, unloading_date_id: tuple, postgres_ex: Pg_extractor):
    """
    Процедуры выгрузки данных из таблицы базы данных  film_work
    в промежуточную базу данных SQLitle для контроля состояния
    и отправка всех данных в Elasticsearch
    :param record_status:
    :param unloading_date_id:
    :param postgres_ex
    """
    unloading_date = unloading_date_id[0][1]
    while True:
        not_loaded_data = record_status.get_all(unloading_date, 0, 'film_work', 'LIMIT 100')
        if len(not_loaded_data) == 0:
            loaded_data = record_status.get_all(unloading_date, 1, 'film_work')
            pg_film = postgres_ex.get_changed_data_table(unloading_date, 'content.film_work', loaded_data)
            if len(pg_film) == 0:
                record_status.up_unloading_date((unloading_date_id[0][0],))
                record_status.set_unloading_date('2022-11-11')
                break
            record_status.set_film_work(pg_film)
            not_loaded_data = tuple(x[0] for x in pg_film)

        data_movies = postgres_ex.extract_all(not_loaded_data, unloading_date)

        movie_array = [Movie_PD(**v) for v in [dict(x) for x in data_movies]]
        query_string = "".join([movie.prin_form() for movie in movie_array])
        es_loader = Loader()
        es_loader.create_index('movies')
        es_loader.store_record('movies', query_string)
        record_status.up_all_film([(x,) for x in not_loaded_data])


def download_data_pg(record_status: SQLiteExtractor, unloading_date: str, postgres_ex: Pg_extractor, param: Param):
    """
    Процедуры выгрузки данных из таблиц базы данных person и genre
    в промежуточную базу данных SQLitle для контроля состояния
    :param record_status:
    :param unloading_date:
    :param postgres_ex:
    :param param:
    """
    while True:
        not_loaded_data = record_status.get_all(unloading_date, 0, param.tab_name)
        if len(not_loaded_data) == 0:
            loaded_data = record_status.get_all(unloading_date, 1, param.tab_name)
            pg_person = postgres_ex.get_changed_data_table(unloading_date, param.content_tab_name, loaded_data)
            if len(pg_person) == 0:
                break
            record_status.set_all(pg_person, param.tab_name)
            not_loaded_data = tuple(x[0] for x in pg_person)

        litle_film = record_status.get_all(unloading_date, 0, 'film_work')
        pg_film = postgres_ex.get_data_film_all(param.content_tab_name_big, param.rek_name, not_loaded_data,
                                                unloading_date, litle_film)
        if len(pg_film) != 0:
            record_status.set_film_work(pg_film)
        data = [(x,) for x in not_loaded_data]
        record_status.up_all(data, param.tab_name)


def load_from_pg(sqlite_conn, pg_conn):
    """
    Основная функция загрузки, здесь создаются экземпляры классов с подключениями
    и вызываются функции по выгрузке данных из БД и загрузки их в Elasticsearch
    :param sqlite_conn:
    :param pg_conn:
    """
    curs = sqlite_conn.cursor()
    record_status = SQLiteExtractor(sqlite_conn, curs)
    postgres_ex = Pg_extractor(pg_conn)

    unloading_date_with_id = record_status.get_last_date()
    unloading_date = unloading_date_with_id[0][1]

    person_param = Param(content_tab_name='content.person', content_tab_name_big='content.person_film_work',
                         tab_name='person', rek_name='person_id')

    genre_param = Param(content_tab_name='content.genre', content_tab_name_big='content.genre_film_work',
                        tab_name='genre', rek_name='genre_id')
    download_data_pg(record_status, unloading_date, postgres_ex, person_param)
    download_data_pg(record_status, unloading_date, postgres_ex, genre_param)
    download_data_film(record_status, unloading_date_with_id, postgres_ex)


def set_timer(timer: int, border_sleep_time: int, factor: int) -> int:
    if timer < border_sleep_time:
        timer = timer * 2 ^ factor
    if timer >= border_sleep_time:
        timer = border_sleep_time
    return timer


def backoff(start_sleep_time: int = 2, factor: int = 2, border_sleep_time: int = 100):
    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            t = start_sleep_time
            while True:
                time.sleep(t)
                try:
                    func(*args)
                    t = start_sleep_time
                except psycopg2.Error:
                    logger_one.exception("psycopg2.Error")
                    t = set_timer(t, border_sleep_time, factor)
                except sqlite3.Error:
                    logger_one.exception("sqlite3.Error")
                    t = set_timer(t, border_sleep_time, factor)
                except elasticsearch.exceptions.ConnectionError:
                    logger_one.exception("elasticsearch.exceptions.ConnectionError")
                    t = set_timer(t, border_sleep_time, factor)
                except Exception:
                    logger_one.exception("Exception")
                    t = set_timer(t, border_sleep_time, factor)

        return inner

    return wrapper


@backoff()
def start_etl():
    dsl = {'dbname': setings_bs.SQL_DATABASE,
           'user': setings_bs.SQL_USER,
           'password': setings_bs.SQL_PASSWORD,
           'host': setings_bs.SQL_HOST,
           'port': setings_bs.SQL_PORT
           }

    with open_db(file_name='db.sqlite') as sqlite_conn, open_pg(dsl) as pg_conn:
        load_from_pg(sqlite_conn, pg_conn)


if __name__ == '__main__':
    while True:
        start_etl()
        time.sleep(setings_bs.time_sleep)
