import uuid
from django.urls import path
from . import views

app_name = 'mealshop'

urlpatterns = [
    path('', views.index, name='index'),
    # Employees menu request
    path('menu/<uuid:uuid>', views.menu, name='menu'),
    path('<int:menu_id>/choose_menu/', views.choose_menu, name='choose_menu'),
    path('<int:menu_id>/add_order', views.add_order, name='add_order'),
    path('view_orders/', views.view_orders, name='view_orders'),
    path('<int:order_id>/add_order_customizations',
         views.add_order_customizations, name='add_order_customizations'),
    # Menu paths
    path('create_menu/',
         views.create_menu, name='create_menu'),
    path('add_menu/',
         views.add_menu, name='add_menu'),
    path('<int:menu_id>/update_daily_menu',
         views.update_daily_menu, name='update_daily_menu'),
    path('daily_menu/', views.daily_menu, name='daily_menu'),
    path('<int:menu_id>/create_reminder', views.create_reminder,
         name='create_reminder'),
    # Menu Option paths
    path('<int:menu_option_id>/menu_option/',
         views.menu_option, name='menu_option'),
    path('<int:menu_option_id>/add_customization/',
         views.add_customization, name='add_customization'),
    path('menu_options/',
         views.menu_options, name='menu_options'),
    path('add_menu_option/',
         views.add_menu_option, name='add_menu_option')
]
