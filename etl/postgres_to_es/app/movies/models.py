import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


class TimeStampedMixin(models.Model):
    created = models.DateTimeField(_('created'), auto_now_add=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)

    class Meta:
        abstract = True


class UUIDMixin(models.Model):
    id = models.UUIDField(_('id'), primary_key=True,
                          default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class Genre(models.Model):
    name = models.CharField(_('name'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    created = models.DateTimeField(_('created'), auto_now_add=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)
    id = models.UUIDField(_('id'), primary_key=True,
                          default=uuid.uuid4, editable=False)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "content\".\"genre"
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'
        indexes = [
            models.Index(fields=['name'], name='film_work_u_genre_idx'),
        ]


class Person(UUIDMixin, TimeStampedMixin):
    full_name = models.TextField(_('full_name'), blank=True)

    def __str__(self):
        return self.full_name

    class Meta:
        db_table = "content\".\"person"
        verbose_name = 'Актер'
        verbose_name_plural = 'Актеры'
        indexes = [
            models.Index(fields=['full_name'], name='film_work_u_person_idx'),
        ]
        constraints = [
            models.UniqueConstraint(fields=['full_name'], name='genre_idx'),
        ]


class Filmwork(UUIDMixin, TimeStampedMixin):

    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    creation_date = models.DateField(_('creation_date'), blank=True)
    rating = models.FloatField(_('rating'), blank=True,
                               validators=[MinValueValidator(0),
                                           MaxValueValidator(100)])
    genre = models.ManyToManyField(Genre, through='GenreFilmwork')
    Persons = models.ManyToManyField(Person, through='PersonFilmwork')
    type = models.TextField(_('type'), blank=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = "content\".\"film_work"
        verbose_name = 'Фильм'
        verbose_name_plural = 'Фильмы'
        indexes = [
            models.Index(fields=['title'], name='film_work_u_idx'),
        ]


class PersonFilmwork(UUIDMixin):

    class Roles(models.TextChoices):
        actor = 'actor', _('actor')
        director = 'director', _('director')
        writer = 'writer', _('writer')

    film_work = models.ForeignKey(Filmwork, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    role = models.TextField(_('role'), null=True, choices=Roles.choices)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "content\".\"person_film_work"
        verbose_name = 'Актер'
        verbose_name_plural = 'Актеры'
        constraints = [
            models.UniqueConstraint(fields=['person_id', 'film_work_id'], name='film_work_person_idx'),
        ]


class GenreFilmwork(UUIDMixin):
    film_work = models.ForeignKey(Filmwork, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "content\".\"genre_film_work"
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'
        constraints = [
            models.UniqueConstraint(fields=['genre_id', 'film_work_id'], name='genre_film_work_idx')
        ]
