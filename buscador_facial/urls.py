from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('registro/', views.registro_view, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('perfil/', views.perfil_view, name='profile'),
    path('logout/', views.logout_view, name='logout'),
    path('reconocer/', views.reconocer_rostro, name='reconocer'),
    path('exportar-logs/', views.export_logs, name='export_logs'),
]
