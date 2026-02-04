from django.db.models import Count
from core.models import Task
from django.utils import timezone
from django.db.models.functions import TruncDate


def task_completion_stats(user):
    qs = Task.objects.filter(user=user)

    total = qs.count()
    completed = qs.filter(status="done").count()
    open_tasks = total - completed

    completion_rate = (
        round((completed / total) * 100, 1) if total > 0 else 0
    )

    by_status = (
        qs.values("status")
        .annotate(count=Count("id"))
    )

    by_priority = (
        qs.values("priority")
        .annotate(count=Count("id"))
    )

    return {
        "total": total,
        "completed": completed,
        "open": open_tasks,
        "completion_rate": completion_rate,
        "by_status": list(by_status),
        "by_priority": list(by_priority),
    }


def weekly_productivity(user):
    today = timezone.now().date()
    start_date = today - timezone.timedelta(days=6)

    qs = (
        Task.objects.filter(
            user=user,
            status="done",
            completed_at__date__range=(start_date, today),
        )
        .annotate(day=TruncDate("completed_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )

    # Convert date objects to strings for JSON serialization
    result = [{"day": str(item["day"]), "count": item["count"]} for item in qs]
    fake = False
    if not result:
        # Sample data for demonstration
        result = [
            {"day": str(today - timezone.timedelta(days=i)), "count": i % 3 + 1}
            for i in range(7)
        ]
        fake = True
    data = {"result": result, "fake": fake}
    # print(data)
    # print(result)
    return data
