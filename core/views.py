from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .models import *
from .forms import TaskForm
from django.utils import timezone
import json
from django.utils.safestring import mark_safe
from core.services.stats import (
    task_completion_stats,
    weekly_productivity,
)

# Create your views here.

def home(request):
    data = {"user": request.user}
    return render(request, "core/home.html", context= data)

@login_required
def task_create(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            if task.status == "done" and not task.completed_at:
                task.completed_at = timezone.now()
            task.save()
            return redirect("task_list")
    else:
        form = TaskForm()
    return render(request, "core/task_form.html", {"form": form})

@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save(commit=False)
            if task.status == "done" and not task.completed_at:
                task.completed_at = timezone.now()
            task.save()
            return redirect("task_list")
    else:
        form = TaskForm(instance=task)
    return render(request, "core/task_form.html", {"form": form})


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == "POST":
        task.delete()
        return redirect("task_list")
    return render(request, "core/task_confirm_delete.html", {"task": task})

@login_required
def task_list(request):
    filter_type = request.GET.get("filter", "week")
    sort_type = request.GET.get("sort", "due_date")

    tasks = Task.objects.filter(user=request.user)
    
    if filter_type == "today":
        tasks = tasks.filter(due_date=timezone.now().date())
    elif filter_type == "week":
        tasks = tasks.filter(
            due_date__lte=timezone.now().date() + timezone.timedelta(days=7)
        )
    elif filter_type == "done":
        tasks = tasks.filter(status="done")
    if sort_type == "due_date":
        tasks = tasks.order_by("due_date")
    elif sort_type == "priority":
        tasks = tasks.order_by("priority")
    else: tasks = tasks.order_by("priority")

    return render(
        request,
        "core/task_list.html",
        {"tasks": tasks, "filter_type": filter_type, "sort_type": sort_type},
    )


@login_required
def stats_view(request):
    print(weekly_productivity(request.user))
    return render(
        request,
        "core/stats.html",
        {
            "stats": task_completion_stats(request.user),
            "weekly_data": (weekly_productivity(request.user)),
        },
    )

def logout_view(request):
    logout(request)
    return redirect("home")