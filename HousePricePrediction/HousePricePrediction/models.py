from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class HouseListing(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='listings',
        null=True  # Temporary to handle existing data
    )
    title = models.CharField(max_length=100)
    price = models.FloatField()
    image = models.ImageField(upload_to='house_images/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    location = models.CharField(max_length=200, blank=True, null=True)
    rooms = models.IntegerField(blank=True, null=True)
    bedrooms = models.IntegerField(blank=True, null=True)
    bathrooms = models.IntegerField(blank=True, null=True)
    area = models.FloatField(blank=True, null=True, help_text="Area in sq. ft.")
    median_income = models.FloatField(blank=True, null=True, help_text="Median income of the locality")
    population = models.IntegerField(blank=True, null=True, help_text="Population of the area")
    house_age = models.IntegerField(blank=True, null=True, help_text="Age of the house in years")
    
    on_sale = models.BooleanField(default=False, help_text="Mark house as currently available for sale")
    featured = models.BooleanField(default=False, help_text="Feature this listing prominently")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'House Listing'
        verbose_name_plural = 'House Listings'

    def __str__(self):
        return self.title


class ScheduleVisit(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    house = models.ForeignKey(HouseListing, on_delete=models.CASCADE, related_name='visits')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scheduled_visits')
    visit_date = models.DateField()
    visit_time = models.TimeField(blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    admin_notes = models.TextField(blank=True, null=True)
    notified = models.BooleanField(default=False, help_text="Has the user been notified of status change?")
    scheduled_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['visit_date', 'visit_time']
        verbose_name = 'Scheduled Visit'
        verbose_name_plural = 'Scheduled Visits'

    def __str__(self):
        return f"{self.user.username} → {self.house.title} on {self.visit_date}"


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('visit', 'Visit Update'),
        ('system', 'System Message'),
        ('admin', 'Admin Alert'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='system')
    link = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def mark_as_read(self):
        self.is_read = True
        self.save()