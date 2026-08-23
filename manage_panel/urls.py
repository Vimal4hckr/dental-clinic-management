from django.urls import path

from . import views

app_name = 'manage_panel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('reports/', views.reports, name='reports'),

    # Users
    path('users/', views.user_list, name='user_list'),
    path('users/new/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_update, name='user_update'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),

    # Generic resources
    path('<slug:slug>/', views.resource_list, name='resource_list'),
    path('<slug:slug>/new/', views.resource_create, name='resource_create'),
    path('<slug:slug>/<int:pk>/edit/', views.resource_update, name='resource_update'),
    path('<slug:slug>/<int:pk>/delete/', views.resource_delete, name='resource_delete'),
]
