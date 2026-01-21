from django.urls import path
from .views import *

urlpatterns = [
    path("", home, name="home"),
    path("tasks/", task_list, name="task_list"),
    path("tasks/new/", task_create, name="task_create"),
    path("tasks/<int:pk>/edit/", task_update, name="task_update"),
    path("tasks/<int:pk>/delete/", task_delete, name="task_delete"),

]
