rundocker:
	@docker-compose -f docker-compose.yml exec db pg_restore -U app -d movies_database /var/bk/pg_dump.sql
	@docker-compose -f docker-compose.yml exec web python manage.py migrate --noinput
