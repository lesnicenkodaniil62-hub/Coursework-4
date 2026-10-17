import random
from datetime import timedelta
from typing import Any

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from clients.models import Client
from mail_messages.models import Message
from mailings.models import Mailing, MailingAttempt


class Command(BaseCommand):
    help = (
        "Тестирует систему рассылок: создаёт тестовые данные, " "выполняет рассылки, формирует отчёт и самоочищается."
    )

    TEST_PREFIX = "test_"
    TEST_EMAIL_DOMAIN = "@test.example.com"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--users",
            type=int,
            default=3,
            help="Количество тестовых пользователей (по умолчанию: 3)",
        )
        parser.add_argument(
            "--clients-per-user",
            type=int,
            default=5,
            help="Количество клиентов на пользователя (по умолчанию: 5)",
        )
        parser.add_argument(
            "--messages-per-user",
            type=int,
            default=3,
            help="Количество сообщений на пользователя (по умолчанию: 3)",
        )
        parser.add_argument(
            "--mailings-per-user",
            type=int,
            default=2,
            help="Количество рассылок на пользователя (по умолчанию: 2)",
        )
        parser.add_argument(
            "--no-cleanup",
            action="store_true",
            help="Не удалять тестовые данные после выполнения",
        )
        parser.add_argument(
            "--cleanup-first",
            action="store_true",
            help="Очистить старые тестовые данные перед запуском",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Основная логика команды."""
        self.stdout.write(self.style.SUCCESS("\n🚀 Начинаем тестирование системы рассылок\n"))

        # Собираем параметры
        users_count: int = options["users"]
        clients_per_user: int = options["clients_per_user"]
        messages_per_user: int = options["messages_per_user"]
        mailings_per_user: int = options["mailings_per_user"]
        no_cleanup: bool = options["no_cleanup"]
        cleanup_first: bool = options["cleanup_first"]

        # Счётчики для отчёта
        stats: dict[str, int] = {
            "users_created": 0,
            "clients_created": 0,
            "messages_created": 0,
            "mailings_created": 0,
            "attempts_success": 0,
            "attempts_failed": 0,
        }

        # Предварительная очистка, если запрошена
        if cleanup_first:
            self.stdout.write(self.style.WARNING("🧹 Предварительная очистка старых тестовых данных..."))
            self._cleanup_by_prefix()

        # Убедимся, что группы существуют
        self._ensure_groups_exist()

        try:
            # Создаём тестовых пользователей и их данные
            test_users = self._create_test_users(
                count=users_count,
                clients_per_user=clients_per_user,
                messages_per_user=messages_per_user,
                mailings_per_user=mailings_per_user,
                stats=stats,
            )

            # Выполняем рассылки
            self._execute_mailings(test_users, stats)

            # Формируем отчёт
            self._print_report(stats)

            # Самоочистка
            if not no_cleanup:
                self._cleanup(test_users)
                self.stdout.write(self.style.SUCCESS("\nТестовые данные удалены\n"))
            else:
                self.stdout.write(self.style.WARNING("\nТестовые данные сохранены (флаг --no-cleanup)\n"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nОшибка при выполнении: {e}\n"))
            if not no_cleanup:
                self.stdout.write(self.style.WARNING("Попытка самоочистки...\n"))
                self._cleanup_by_prefix()
            raise

    def _ensure_groups_exist(self) -> None:
        """Создаёт группы, если их нет."""
        Group.objects.get_or_create(name="Пользователь")
        Group.objects.get_or_create(name="Менеджер")
        self.stdout.write("✓ Группы 'Пользователь' и 'Менеджер' проверены")

    def _create_test_users(
        self,
        count: int,
        clients_per_user: int,
        messages_per_user: int,
        mailings_per_user: int,
        stats: dict[str, int],
    ) -> list[User]:
        """Создаёт тестовых пользователей с данными."""
        test_users: list[User] = []

        for i in range(1, count + 1):
            username = f"{self.TEST_PREFIX}user_{i}"
            email = f"{username}{self.TEST_EMAIL_DOMAIN}"
            password = "testpassword123"

            # Используем get_or_create для идемпотентности
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "is_active": True,
                },
            )
            if created:
                user.set_password(password)
                user.save()
                stats["users_created"] += 1
                self.stdout.write(f"Пользователь '{username}' создан")
            else:
                self.stdout.write(f"Пользователь '{username}' уже существует, используем его")

            # Убедимся, что пользователь в группе "Пользователь"
            user_group = Group.objects.get(name="Пользователь")
            user.groups.add(user_group)

            # Создаём клиентов
            self._create_test_clients(user, clients_per_user, stats)

            # Создаём сообщения
            self._create_test_messages(user, messages_per_user, stats)

            # Создаём рассылки
            self._create_test_mailings(user, mailings_per_user, stats)

            test_users.append(user)

        return test_users

    def _create_test_clients(self, user: User, count: int, stats: dict[str, int]) -> None:
        """Создаёт тестовых клиентов для пользователя."""
        for i in range(1, count + 1):
            email = f"{self.TEST_PREFIX}client_{user.pk}_{i}{self.TEST_EMAIL_DOMAIN}"
            # Проверяем, не создан ли уже такой клиент
            if Client.objects.filter(email=email).exists():
                continue

            Client.objects.create(
                email=email,
                full_name=f"Тестовый Клиент {i} (Пользователь {user.pk})",
                comment=f"Создан командой test_mailing_system для пользователя {user.username}",
                owner=user,
            )
            stats["clients_created"] += 1

    def _create_test_messages(self, user: User, count: int, stats: dict[str, int]) -> None:
        """Создаёт тестовые сообщения для пользователя."""
        for i in range(1, count + 1):
            subject = f"Тестовое сообщение {i} от {user.username}"
            # Проверяем, не создано ли уже такое сообщение
            if Message.objects.filter(subject=subject, owner=user).exists():
                continue

            Message.objects.create(
                subject=subject,
                body=(
                    f"Здравствуйте!\n\n"
                    f"Это тестовое сообщение #{i} от пользователя {user.username}.\n\n"
                    f"Создано командой test_mailing_system.\n\n"
                    f"С уважением,\nКоманда Messenger"
                ),
                owner=user,
            )
            stats["messages_created"] += 1

    def _create_test_mailings(self, user: User, count: int, stats: dict[str, int]) -> None:
        """Создаёт тестовые рассылки для пользователя."""
        now = timezone.now()
        clients = list(Client.objects.filter(owner=user))
        messages = list(Message.objects.filter(owner=user))

        if not clients or not messages:
            return

        # Если у пользователя уже есть рассылки, не создаём новые
        existing_mailings_count = Mailing.objects.filter(owner=user).count()
        if existing_mailings_count >= count:
            return

        for i in range(existing_mailings_count + 1, count + 1):
            # Чередование: одна рассылка активная, другая будущая
            if i % 2 == 1:
                # Активная рассылка (в текущем временном окне)
                start_time = now - timedelta(hours=1)
                end_time = now + timedelta(hours=23)
                status = Mailing.STATUS_RUNNING
            else:
                # Будущая рассылка
                start_time = now + timedelta(days=7)
                end_time = now + timedelta(days=14)
                status = Mailing.STATUS_CREATED

            mailing = Mailing.objects.create(
                start_time=start_time,
                end_time=end_time,
                status=status,
                message=messages[i % len(messages)],
                owner=user,
            )
            mailing.recipients.set(clients)
            stats["mailings_created"] += 1

    def _execute_mailings(self, test_users: list[User], stats: dict[str, int]) -> None:
        """Выполняет тестовые рассылки (создаёт попытки)."""
        self.stdout.write("\nВыполняем рассылки...")

        for user in test_users:
            active_mailings = Mailing.objects.filter(
                owner=user,
                status=Mailing.STATUS_RUNNING,
            )

            for mailing in active_mailings:
                # Пропускаем рассылки, у которых уже есть попытки
                if mailing.attempts.exists():  # type: ignore[attr-defined]
                    continue

                recipients = mailing.recipients.all()
                for client in recipients:
                    # Имитация отправки: 80% успех, 20% ошибка
                    if random.random() < 0.8:
                        MailingAttempt.objects.create(
                            mailing=mailing,
                            status=MailingAttempt.STATUS_SUCCESS,
                            server_response="250 OK: Письмо принято к отправке",
                        )
                        stats["attempts_success"] += 1
                    else:
                        MailingAttempt.objects.create(
                            mailing=mailing,
                            status=MailingAttempt.STATUS_FAILED,
                            server_response="550 Error: Адресат не найден",
                        )
                        stats["attempts_failed"] += 1

            self.stdout.write(f"✓ Обработано рассылок пользователя '{user.username}': {active_mailings.count()}")

    def _print_report(self, stats: dict[str, int]) -> None:
        """Формирует красивый отчёт."""
        total_attempts = stats["attempts_success"] + stats["attempts_failed"]
        success_rate = (stats["attempts_success"] / total_attempts * 100) if total_attempts > 0 else 0

        self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
        self.stdout.write(self.style.SUCCESS("📊 ОТЧЁТ О ТЕСТИРОВАНИИ"))
        self.stdout.write(self.style.SUCCESS("=" * 60))

        self.stdout.write(f"\nСоздано пользователей:        {stats['users_created']}")
        self.stdout.write(f"Создано клиентов:           {stats['clients_created']}")
        self.stdout.write(f"Создано сообщений:          {stats['messages_created']}")
        self.stdout.write(f"Создано рассылок:           {stats['mailings_created']}")

        self.stdout.write(f"\nУспешных попыток отправки:   {stats['attempts_success']}")
        self.stdout.write(f"Неуспешных попыток:          {stats['attempts_failed']}")
        self.stdout.write(f"Процент успешных отправок:   {success_rate:.1f}%")

        self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
        self.stdout.write(self.style.SUCCESS("🎉 Тестирование завершено успешно!"))
        self.stdout.write(self.style.SUCCESS("=" * 60 + "\n"))

    def _cleanup(self, test_users: list[User]) -> None:
        """Удаляет тестовые данные по списку пользователей."""
        with transaction.atomic():
            for user in test_users:
                # Удаляем попытки рассылок
                MailingAttempt.objects.filter(mailing__owner=user).delete()
                # Удаляем рассылки
                Mailing.objects.filter(owner=user).delete()
                # Удаляем сообщения
                Message.objects.filter(owner=user).delete()
                # Удаляем клиентов
                Client.objects.filter(owner=user).delete()
                # Удаляем пользователя
                user.delete()

    def _cleanup_by_prefix(self) -> None:
        """Удаляет тестовые данные по префиксу (для экстренной очистки)."""
        with transaction.atomic():
            # Находим всех тестовых пользователей
            test_users = User.objects.filter(username__startswith=self.TEST_PREFIX)
            count = test_users.count()

            for user in test_users:
                MailingAttempt.objects.filter(mailing__owner=user).delete()
                Mailing.objects.filter(owner=user).delete()
                Message.objects.filter(owner=user).delete()
                Client.objects.filter(owner=user).delete()
                user.delete()

            self.stdout.write(self.style.WARNING(f"Удалено тестовых пользователей: {count}"))
