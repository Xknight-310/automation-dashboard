from django.core.mail import send_mail
from django.utils import timezone
from .models import Task

def send_overdue_task_reminders():
    today = timezone.now().date()

    overdue_tasks = Task.objects.filter(
        due_date__lt=today,
        status__in=["todo", "doing"],
    ).select_related("user")

    users = {}

    for task in overdue_tasks:
        users.setdefault(task.user, []).append(task)

    for user, tasks in users.items():
        subject = "You have overdue tasks"
        message = "These tasks are overdue:\n\n"

        for task in tasks:
            message += f"- {task.title} (due {task.due_date})\n"

        send_mail(
            subject,
            message,
            None,
            [user.email],
        )
