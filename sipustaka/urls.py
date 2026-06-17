"""
URL configuration for sipustaka project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from perpus import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard_view, name='dashboard'),
    
    path('users/', views.users_view, name='users'),
    path('users/add/', views.add_user_view, name='add_user'),
    
    path('buku/', views.buku_view, name='buku'),
    path('buku/add/', views.add_buku_view, name='add_buku'),
    
    # RUTE MODUL PEMINJAMAN BARU
    path('pinjam/', views.pinjam_view, name='pinjam'),
    path('peminjaman/add/', views.add_pinjam_view, name='add_pinjam'),
    path('peminjaman/kembali/<int:pinjam_id>/', views.kembalikan_buku_view, name='kembalikan_buku'),

    # RUTE TAMBAHAN UNTUK AKSI BUKU
    path('buku/detail/<int:buku_id>/', views.detail_buku_view, name='detail_buku'),
    path('buku/edit/<int:buku_id>/', views.edit_buku_view, name='edit_buku'),
    path('buku/hapus/<int:buku_id>/', views.hapus_buku_view, name='hapus_buku'),

    # RUTE MODUL USER (TAMBAHAN DETAIL, EDIT, HAPUS)
    path('user/detail/<int:user_id>/', views.detail_user_view, name='detail_user'),
    path('user/edit/<int:user_id>/', views.edit_user_view, name='edit_user'),
    path('user/hapus/<int:user_id>/', views.hapus_user_view, name='hapus_user'),
]