from django.contrib import admin
from .models import HouseListing, ScheduleVisit, Notification
from django.utils.html import format_html


@admin.register(HouseListing)
class HouseListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'location', 'bedrooms', 'rooms', 'area', 'house_age', 'on_sale', 'created_at')
    search_fields = ('title', 'location')
    list_filter = ('on_sale', 'created_at')
    list_editable = ('on_sale',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('title', 'price', 'image', 'description', 'on_sale')
        }),
        ('Property Details', {
            'fields': ('location', 'bedrooms', 'rooms', 'bathrooms', 'area', 'house_age')
        }),
        ('Local Area Info', {
            'fields': ('median_income', 'population')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ScheduleVisit)
class ScheduleVisitAdmin(admin.ModelAdmin):
    list_display = ('user', 'house', 'visit_date', 'visit_time', 'status_badge', 'scheduled_at', 'admin_notes_preview')
    list_filter = ('status', 'visit_date')
    search_fields = ('user__username', 'house__title', 'admin_notes')
    ordering = ('-scheduled_at',)
    actions = ['approve_selected', 'reject_selected', 'mark_as_completed']
    readonly_fields = ('scheduled_at', 'updated_at')
    list_per_page = 20

    fieldsets = (
        (None, {
            'fields': ('user', 'house', 'status')
        }),
        ('Visit Details', {
            'fields': ('visit_date', 'visit_time', 'message')
        }),
        ('Admin Section', {
            'fields': ('admin_notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('scheduled_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        color_map = {
            'pending': 'orange',
            'approved': 'green',
            'rejected': 'red',
            'completed': 'blue',
            'cancelled': 'gray'
        }
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; border-radius: 4px;">{}</span>',
            color_map.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'

    def admin_notes_preview(self, obj):
        return obj.admin_notes[:50] + '...' if obj.admin_notes else '-'
    admin_notes_preview.short_description = 'Admin Notes'

    def approve_selected(self, request, queryset):
        count = 0
        for visit in queryset.filter(status='pending'):
            visit.status = 'approved'
            visit.save()
            Notification.objects.create(
                user=visit.user,
                message=f"✅ Your visit to '{visit.house.title}' on {visit.visit_date} at {visit.visit_time} has been approved!",
                link='/notifications/',
                notification_type='success'
            )
            count += 1
        self.message_user(request, f"{count} visit(s) approved and user(s) notified.")
    approve_selected.short_description = "Approve selected visits"

    def reject_selected(self, request, queryset):
        count = 0
        for visit in queryset.filter(status='pending'):
            visit.status = 'rejected'
            visit.admin_notes = visit.admin_notes or "Rejected by admin."
            visit.save()
            Notification.objects.create(
                user=visit.user,
                message=f"❌ Your visit to '{visit.house.title}' was rejected. Reason: {visit.admin_notes}",
                link='/notifications/',
                notification_type='alert'
            )
            count += 1
        self.message_user(request, f"{count} visit(s) rejected and user(s) notified.")
    reject_selected.short_description = "Reject selected visits"

    def mark_as_completed(self, request, queryset):
        updated = queryset.filter(status='approved').update(status='completed')
        self.message_user(request, f"{updated} visit(s) marked as completed.")
    mark_as_completed.short_description = "Mark as completed"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message_preview', 'is_read', 'created_at', 'link_preview')
    list_filter = ('is_read', 'user')
    search_fields = ('message', 'user__username')
    list_editable = ('is_read',)
    actions = ['mark_as_read', 'mark_as_unread']
    list_per_page = 20

    def message_preview(self, obj):
        return obj.message[:60] + '...' if len(obj.message) > 60 else obj.message
    message_preview.short_description = 'Message'

    def link_preview(self, obj):
        return obj.link[:30] + '...' if obj.link else '-'
    link_preview.short_description = 'Link'

    def is_read_badge(self, obj):
        color = 'green' if obj.is_read else 'red'
        text = 'Read' if obj.is_read else 'Unread'
        return format_html(
            '<span style="color: white; background-color: {}; padding: 2px 6px; border-radius: 4px;">{}</span>',
            color, text
        )
    is_read_badge.short_description = 'Status'
    is_read_badge.admin_order_field = 'is_read'

    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} notification(s) marked as read.")
    mark_as_read.short_description = "Mark as read"

    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f"{updated} notification(s) marked as unread.")
    mark_as_unread.short_description = "Mark as unread"
