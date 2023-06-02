import json
import pathlib
from pathlib import Path

from elasticsearch import Elasticsearch

from ETL_settings import Settings_BS

setings_bs = Settings_BS()


class Loader:
    def __init__(self):
        self.es = Elasticsearch([
            {
                'host': setings_bs.EL_HOST,
                'port': setings_bs.EL_PORT
            }
        ])

    def create_index(self, index_name: str):
        """
        Создаем инде по заданной схеме
        :param index_name: имя индекса
        """
        dir_path = pathlib.Path.cwd()
        path = Path(dir_path, 'es_schema.json')
        with open(path, 'r') as f:
            settings = json.load(f)
            if not self.es.indices.exists(index_name):
                self.es.indices.create(index=index_name, ignore=400, body=settings)

    def store_record(self, index_name: str, record: str):
        """
        Основная процедура загруки данных в Elasticsearch
        :param index_name: имя индекса куда грузим
        :param record: Строка загрузки которая формирует документы
        """

        self.es.bulk(index=index_name, body=record)
