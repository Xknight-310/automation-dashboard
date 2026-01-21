from django.core.management.base import BaseCommand
from core.emails import send_overdue_task_reminders

class Command(BaseCommand):
    help = "Send email reminders for overdue tasks"

    def handle(self, *args, **kwargs):
        send_overdue_task_reminders()
        self.stdout.write(self.style.SUCCESS("Overdue task emails sent"))
