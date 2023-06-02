from dataclasses import dataclass
from datetime import datetime
from pydantic.schema import Optional
from pydantic import BaseModel, validator


class Movie_PD(BaseModel):
    id: str
    title: str
    imdb_rating: Optional[float]
    type_m: str
    description: str
    created: datetime
    modified: datetime
    persons: list
    genres: list

    @validator('description')
    def description_check(cls, v):
        v = v.replace("'", "")
        v = v.replace('"', "")
        return v

    @validator('title')
    def persons_check(cls, v):
        v = v.replace("'", "")
        v = v.replace('"', "")
        return v

    @validator('imdb_rating')
    def imdb_rating_check(cls, v):
        if v is None:
            v = 0.0
        return v

    def prin_form(self):
        """
        Процедура формирования строки для загрузки в Elasticsearch
        """
        sekond_str = {"id": self.id, "imdb_rating": self.imdb_rating, "genre": ([(x) for x in self.genres]),
                      "title": self.title, "description": self.description,
                      "director": ",".join(
                          [x['person_name'].replace('"', "") for x in self.persons if x['person_role'] == 'director']),
                      "actors_names": ", ".join(
                          [x['person_name'].replace('"', "") for x in self.persons if x['person_role'] == 'actor']),
                      "writers_names": [", ".join(
                          [x['person_name'].replace('"', "") for x in self.persons if x['person_role'] == 'writer'])],
                      "actors": [{'id': x['person_id'], 'name': x['person_name'].replace('"', "")} for x in self.persons
                                 if x['person_role'] == 'actor'],
                      "writers": [{'id': x['person_id'], 'name': x['person_name'].replace('"', "")} for x in
                                  self.persons if x['person_role'] == 'writer']}

        first_str = {"index": {"_index": "movies", "_id": self.id}}
        it = f"""{first_str}
                 {sekond_str}
              """
        return it.replace("'", '"')


@dataclass
class Param:
    content_tab_name: str
    content_tab_name_big: str
    tab_name: str
    rek_name: str
