from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q
from django.http import JsonResponse
from django.views.generic.detail import BaseDetailView
from django.views.generic.list import BaseListView
from movies.models import Filmwork


class MoviesApiMixin:
    model = Filmwork
    http_method_names = ['get']

    def get_queryset(self):
        data = Filmwork.objects.all().annotate(
            genres=ArrayAgg('genre__name', distinct=True),
            actors=self.get_person_aggregation('actor'),
            directors=self.get_person_aggregation('director'),
            writers=self.get_person_aggregation('writer'),
        ).values('id', 'title', 'description', 'creation_date', 'rating', 'type', 'genres', 'actors',
                 'directors', 'writers'
                 )
        return data

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(context)

    def get_person_aggregation(self, role_type):
        return ArrayAgg('Persons__full_name', distinct=True, filter=Q(personfilmwork__role=role_type))


class MoviesListApi(MoviesApiMixin, BaseListView):
    paginate_by = 50

    def get_context_data(self, *, object_list=None, **kwargs):
        queryset = self.get_queryset()
        paginator, page, queryset, is_paginated = self.paginate_queryset(queryset, self.paginate_by)
        pg_previous_page_number = None
        if page.has_previous():
            pg_previous_page_number = page.previous_page_number()

        pg_next_page_number = None
        if page.has_next():
            pg_next_page_number = page.next_page_number()

        context = {
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'prev': pg_previous_page_number,
            'next': pg_next_page_number,
            'results': list(queryset),
        }
        return context


class MoviesDetailApi(MoviesApiMixin, BaseDetailView):

    def get_context_data(self, **kwargs):
        return kwargs['object']
