from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Authentication
    path('', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),

    # Core Pages
    path('home/', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    # Prediction System
    path('predict/', views.predict, name='predict'),
    path('result/', views.result, name='result'),
    path('heatmap/', views.show_heatmap, name='heatmap'),

    # Property Listings
    path('listings/', views.listings_view, name='listings'),
    path('listings/<int:pk>/', views.house_detail, name='house_detail'),
    path('listings/<int:pk>/mark/', views.mark_for_sale, name='mark_for_sale'),

    # Visit Scheduling (Only creation by user; no cancellation by user)
    path('schedule-visit/<int:house_id>/', views.schedule_visit, name='schedule_visit'),

    # Notification System
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/clear/', views.clear_notifications, name='clear_notifications'),
    path('check-notifications/', views.check_notifications, name='check_notifications'),

    # Admin Visit Approvals
    path('admin/visit-approvals/', views.admin_visit_approvals, name='admin_visit_approvals'),
    path('admin/approve-visit/<int:visit_id>/', views.approve_visit, name='approve_visit'),
    path('admin/reject-visit/<int:visit_id>/', views.reject_visit, name='reject_visit'),

    # AJAX Endpoint
    path('check-visit-status/<int:house_id>/', views.check_visit_status, name='check_visit_status'),

    # Django Admin
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
