from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import *
from .forms import TaskForm
from django.utils import timezone

# Create your views here.

def home(request):
    data = {"username": request.user.id}
    return render(request, "core/home.html", context= data)

@login_required
def task_create(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
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
            form.save()
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
    filter_type = request.GET.get("filter")

    tasks = Task.objects.filter(user=request.user)
    if filter_type == "last_week":
        tasks = tasks.filter(
            due_date__lte=timezone.now().date() + timezone.timedelta(days=-7)
            )
    elif filter_type == "today":
        tasks = tasks.filter(due_date=timezone.now().date())
    elif filter_type == "week":
        tasks = tasks.filter(
            due_date__lte=timezone.now().date() + timezone.timedelta(days=7)
        )
    elif filter_type == "done":
        tasks = tasks.filter(status="done")
    tasks = tasks.order_by("due_date")

    return render(
        request,
        "core/task_list.html",
        {"tasks": tasks, "filter_type": filter_type},
    )
