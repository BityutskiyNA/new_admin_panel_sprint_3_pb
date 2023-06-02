import datetime


def attention(sender, instance, created, **kwargs):
    if created and instance.creation_date == datetime.date.today():
        print(f"Сегодня премьера {instance.title}! 🥳")
