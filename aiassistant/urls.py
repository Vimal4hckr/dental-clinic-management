from django.urls import path

from . import views

app_name = 'aiassistant'

urlpatterns = [
    path('', views.hub, name='hub'),
    path('symptom-checker/', views.symptom_checker, name='symptom_checker'),
    path('chatbot/', views.chatbot, name='chatbot'),
    path('chatbot/api/', views.chatbot_api, name='chatbot_api'),
    path('cost-estimator/', views.cost_estimator, name='cost_estimator'),
]
