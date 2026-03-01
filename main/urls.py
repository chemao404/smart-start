from django.contrib import admin
from django.urls import path

from main.views import *
app_name = 'main'
urlpatterns = [
   path("",index,name="index"),
   path("teachers", teacher_list, name="teacher_list"),
   path("contact", contact, name="contact"),

   path('news_list', NewsListView.as_view(), name='news_list'),
   path('news_list/<int:pk>/', NewsDetailView.as_view(), name='news_detail'),
   path('create/', NewsCreateView.as_view(), name='news_create'),
   path('<int:pk>/update/', NewsUpdateView.as_view(), name='news_update'),
   path('<int:pk>/delete/', NewsDeleteView.as_view(), name='news_delete'),   path('dashboard', dashboard, name='dashboard'),

   path('approve-teacher/<int:teacher_id>/', approve_teacher, name='approve_teacher'),
   path('teachers/<int:teacher_id>/apply/', create_application, name='create_application'),
   path('my-applications/', student_applications, name='student_applications'),
   path('teacher-applications/', teacher_applications, name='teacher_applications'),
   path('application/<int:application_id>/handle/', handle_application, name='handle_application'),

]
