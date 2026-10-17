from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Создаёт группы 'Пользователь' и 'Менеджер'"

    def handle(self, *args, **kwargs):
        user_group, created = Group.objects.get_or_create(name="Пользователь")
        if created:
            self.stdout.write(self.style.SUCCESS("Группа 'Пользователь' создана"))
        else:
            self.stdout.write("Группа 'Пользователь' уже существует")

        manager_group, created = Group.objects.get_or_create(name="Менеджер")
        if created:
            self.stdout.write(self.style.SUCCESS("Группа 'Менеджер' создана"))
        else:
            self.stdout.write("Группа 'Менеджер' уже существует")

        self.stdout.write(self.style.SUCCESS("Готово!"))
