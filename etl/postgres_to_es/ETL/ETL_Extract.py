class Pg_extractor:
    def __init__(self, pg_conn):
        self.pg_conn = pg_conn

    def extract_all(self, data: list, date_ex: str):
        """
        Основной запрос с данными по фильму из базы данных.
        :param data: список id фильмов
        :param date_ex: дата более которой идет выборка
        """
        curs = self.pg_conn.cursor()
        text_sql = """SELECT
                       fw.id,
                       fw.title,
                       fw.description,
                       fw.rating as imdb_rating,
                       fw.type as type_m,
                       fw.created,
                       fw.modified,
                       COALESCE (
                           json_agg(
                               DISTINCT jsonb_build_object(
                                   'person_role', pfw.role,
                                   'person_id', p.id,
                                   'person_name', p.full_name
                               )
                           ) FILTER (WHERE p.id is not null),
                           '[]'
                       ) as persons,
                       array_agg(DISTINCT g.name) as genres
                    FROM content.film_work fw
                    LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
                    LEFT JOIN content.person p ON p.id = pfw.person_id
                    LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id
                    LEFT JOIN content.genre g ON g.id = gfw.genre_id
                    WHERE fw.modified > %s and fw.id IN %s
                    GROUP BY fw.id;"""
        curs.execute(text_sql, (date_ex, data,))
        return curs

    def get_changed_data_table(self, date_ex: str, table_name: str, ids: tuple) -> list:
        """
        Получаем данные из таблицы id и дату изменния
        :param table_name: имя таблицы
        :param date_ex: дата больше которой читаем измения
        :param ids: список id которые уже выгружены и не должны попасть в выборку
        """
        if len(ids) == 0:
            ids = ('00000000-0000-0000-0000-000000000000',)
        curs = self.pg_conn.cursor()
        sql_text = """SELECT id, modified
                        FROM {0}
                        WHERE modified >  %s and id not in %s
                        ORDER BY modified
                        LIMIT 100;""".format(table_name)
        curs.execute(sql_text, (date_ex, ids))
        records = curs.fetchall()
        return [(x[0], x[1], date_ex, False) for x in records]

    def get_data_film_all(self, table_name: str, prop_name: str, date_ex: tuple, unloading_date: str,
                          films: tuple) -> list:
        """
        Получаем список film_work_id из таблицы person_film_work или genre_film_work
        которые есть в date_ex но их нет среди уже выгруженных фильмов
        :param table_name: имя таблицы
        :param prop_name: имя поараметра по которому проверяме
        :param date_ex: список id таблицы которые нужно получить
        :param unloading_date: дата вставляемая в результат
        :param films: id которые уже были выгружены
        """
        if len(films) == 0:
            films = ('00000000-0000-0000-0000-000000000000',)
        curs = self.pg_conn.cursor()
        sql_text = """SELECT film_work_id
                        FROM {0}
                        WHERE {1} in %s and film_work_id not in %s;""".format(table_name, prop_name)
        curs.execute(sql_text, (date_ex, films))
        data = curs.fetchall()
        return [(x[0], unloading_date, unloading_date, False) for x in data]


class SQLiteExtractor:
    def __init__(self, connection=None, curs=None):
        self.connection = connection
        self.curs = curs

        exists_buffer = self.test_by_table()
        if exists_buffer == 0:
            self.create_table('film_work')
            self.create_table('genre')
            self.create_table('person')
            self.create_table('sync_date')
            self.set_unloading_date('1900-01-01')

    def create_table(self, table_name: str):
        """
        Процедура создает таблицу с переданным названием
        :param table_name: имя таблицы
        """
        self.curs.execute('''CREATE TABLE {0} (
                                   id INTEGER PRIMARY KEY,
                                   id_obj TEXT ,
                                   modified datetime,
                                   unloading_date datetime,
                                   done int);'''.format(table_name))
        self.connection.commit()

    def create_table_unloading_date(self):
        """
        Процедура создает таблицу для хранения даты выгрузки
        """
        self.curs.execute("""CREATE TABLE sync_date (
                                id INTEGER PRIMARY KEY,
                                unloading_date datetime,
                                done int);""")
        self.connection.commit()

    def set_unloading_date(self, unloading_date: str):
        """
        Процедура обновляет таблицу для хранения даты выгрузки
        :param unloading_date: дата выборки по которой будем отбирать модифицированные объекты
        """
        sqlite_insert_with_param = """INSERT INTO sync_date
                                                 (unloading_date, done)
                                                 VALUES (?, ?);"""
        data_tuple = (unloading_date, 0)
        self.curs.execute(sqlite_insert_with_param, data_tuple)
        self.connection.commit()

    def set_film_work(self, records: list):
        """
        Процедура записи данных по заданному массиву records
        :param records: массив с параметрами для записи в таблицу
        """
        sqlite_insert_query = """INSERT INTO film_work
                                         (id_obj, modified, unloading_date, done)
                                         VALUES (?, ?, ?, ?);"""
        self.curs.executemany(sqlite_insert_query, records)
        self.connection.commit()

    def up_all_film(self, data: list):
        """
        Устанавливаем значение параметра dane для указаных id в таблице film_work
        :param data: список id которые нужно обновить
        """
        sql_update_query = """Update film_work set done = 1 where id_obj = ?"""
        self.curs.executemany(sql_update_query, data)
        self.connection.commit()

    def test_by_table(self) -> int:
        """
        Процедура проверяет есть ли таблица film_work в базе данных
        """
        sqlite_select_query = """SELECT name FROM sqlite_master WHERE type='table' AND name='film_work';"""
        self.curs.execute(sqlite_select_query)
        return len(self.curs.fetchall())

    def get_last_date(self) -> tuple:
        """
        Функция возвращает последнюю дату по которой смотрим был ли изменен объект
        """
        sqlite_select_query = """SELECT id, unloading_date  from sync_date where done = 0"""
        self.curs.execute(sqlite_select_query)
        return tuple(x for x in self.curs.fetchall())

    def up_unloading_date(self, data: tuple):
        """
        Обновляем таблицу sync_date проставляем в параметре done = 1
        :param data: id даты которую надо обновить
        """
        sql_update_query = """Update sync_date set done = 1 where id = ?"""
        self.curs.execute(sql_update_query, data)
        self.connection.commit()

    def get_all(self, unloading_date: str, done: int, table_name: str, limit: str = "") -> tuple:
        """
        Функция возвращет все id из таблицы за указаную дату с определенным значением
        done, для проверки был объект выгружен в Elasticsearch или нет
        :param unloading_date: дата за которую происходят изменения
        :param done: значение параметры был ли выгружен объект или нет
        :param table_name: имя таблицы
        :param limit: лимит записей по умолчанию пустой
        """
        sqlite_select_query = """SELECT id_obj from {0}
                                where done = ? and unloading_date = ?
                                {1}""".format(table_name, limit)
        self.curs.execute(sqlite_select_query, (done, unloading_date))
        return tuple(x[0] for x in self.curs.fetchall())

    def set_all(self, records: list, table_name: str):
        """
        Процедура обновляет данные таблицы id_obj, modified, unloading_date, done
        :param records: списк данных который грузим
        :param table_name: имя таблицы в которую грузим данные
        """
        sqlite_insert_query = """INSERT INTO {0}
                                         (id_obj, modified, unloading_date, done)
                                         VALUES (?, ?, ?, ?);""".format(table_name)
        self.curs.executemany(sqlite_insert_query, records)
        self.connection.commit()

    def up_all(self, data: list, table_name: str):
        """
        Обновляем данные в таблице и устанавливаем значение реквизита done = 1
        :param data: список id которые будем обновлять
        :param table_name: имя таблицы
        """
        sql_update_query = """Update {0} set done = 1 where id_obj = ?""".format(table_name)
        self.curs.executemany(sql_update_query, data)
        self.connection.commit()
