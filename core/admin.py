from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.utils import timezone
from .models import *

# -----------------------------
# Generic Inline for Reports
# -----------------------------
class ReportInline(GenericTabularInline):
    model = Report
    ct_field = 'content_type'       # ✅ Important fix
    ct_fk_field = 'object_id'
    extra = 0

# -----------------------------
# Custom User Admin
# -----------------------------
class CustomUserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'level', 'public_profile', 'date_joined')
    list_filter = ('role__role_type', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    readonly_fields = ('required_points',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'gender', 'bio', 'location', 'photo')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions', 'role')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
        ('Gamification', {'fields': ('points', 'level', 'public_profile', 'required_points')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'gender', 'password1', 'password2'),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(role__role_type='A')
        return qs

@admin.register(User)
class CustomUserAdminRegistration(CustomUserAdmin):
    pass

# -----------------------------
# Role Admin
# -----------------------------
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'role_type', 'description')
    list_filter = ('role_type',)
    search_fields = ('name',)
    actions = ['delete_role']

    def delete_role(self, request, queryset):
        if request.user.is_superuser:
            queryset.delete()

# -----------------------------
# Category Admin
# -----------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type', 'post_count', 'note_count')
    list_filter = ('category_type',)
    search_fields = ('name',)
    actions = ['delete_category']

    def post_count(self, obj):
        return obj.forumpost_set.count()
    post_count.short_description = 'Forum Posts'

    def note_count(self, obj):
        return obj.studentnote_set.count()
    note_count.short_description = 'Student Notes'

    def delete_category(self, request, queryset):
        queryset.delete()

# -----------------------------
# Forum Post Admin
# -----------------------------
@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'created_on', 'reply_count', 'removed')
    list_filter = ('category', 'removed', 'created_on')
    search_fields = ('title', 'content')
    inlines = [ReportInline]
    actions = ['mark_as_removed']

    def mark_as_removed(self, request, queryset):
        queryset.update(removed=True, removal_reason="Removed by admin", modified_by=request.user)

# -----------------------------
# Student Note Admin
# -----------------------------
@admin.register(StudentNote)
class StudentNoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'removed')
    list_filter = ('category', 'removed')
    search_fields = ('title', 'content')
    inlines = [ReportInline]
    actions = ['remove_notes']

    def remove_notes(self, request, queryset):
        queryset.update(removed=True)

# -----------------------------
# Comment Admin (✅ fixed!)
# -----------------------------
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'content', 'created_on', 'removed')
    list_filter = ('removed',)
    search_fields = ('content', 'author__username')
    inlines = [ReportInline]  # ✅ Works now with updated ct_field and ct_fk_field

# -----------------------------
# Textbook Admin
# -----------------------------
@admin.register(Textbook)
class TextbookAdmin(admin.ModelAdmin):
    list_display = ('title', 'isbn', 'current_stock', 'locations_list')
    list_filter = ('relevant_categories',)
    search_fields = ('title', 'isbn')
    filter_horizontal = ('locations', 'relevant_categories')

    def current_stock(self, obj):
        return obj.stock
    current_stock.short_description = 'Stock'

    def locations_list(self, obj):
        return ", ".join([loc.name for loc in obj.locations.all()])
    locations_list.short_description = 'Locations'

# -----------------------------
# Textbook Request Admin
# -----------------------------
@admin.register(TextbookRequest)
class TextbookRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'textbook', 'status', 'created_on', 'fulfillment_date')
    list_filter = ('status', 'created_on')
    search_fields = ('user__username', 'textbook__title')
    actions = ['approve_requests']

    def save_model(self, request, obj, form, change):
        if obj.status == 'A' and obj.textbook.stock > 0:
            TextbookStockHistory.objects.create(
                textbook=obj.textbook,
                admin=request.user,
                old_stock=obj.textbook.stock,
                new_stock=obj.textbook.stock - 1
            )
            obj.textbook.stock -= 1
            obj.textbook.save()
        super().save_model(request, obj, form, change)

    def approve_requests(self, request, queryset):
        queryset.update(status='A', fulfillment_date=timezone.now())

# -----------------------------
# Drop Location Admin
# -----------------------------
@admin.register(DropLocation)
class DropLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'lat', 'lng')
    search_fields = ('name', 'address')

# -----------------------------
# Report Admin
# -----------------------------
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('content_object', 'reporter', 'status', 'created_on', 'resolved_at')
    list_filter = ('status', 'content_type')
    list_editable = ('status',)
    search_fields = ('reason', 'reporter__username')
    readonly_fields = ('resolved_at',)
    actions = ['mark_resolved']

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['unresolved_count'] = Report.objects.filter(status='U').count()
        extra_context['resolved_count'] = Report.objects.filter(status='R').count()
        return super().changelist_view(request, extra_context=extra_context)

    def mark_resolved(self, request, queryset):
        queryset.update(status='R', resolved_at=timezone.now())

# -----------------------------
# Notification Admin
# -----------------------------
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'read', 'created_on')
    list_filter = ('notification_type', 'read')
    search_fields = ('user__username', 'message')

# -----------------------------
# Donation Admin
# -----------------------------
@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'amount', 'completed', 'receipt_email', 'created_on')
    list_filter = ('completed', 'created_on')
    search_fields = ('first_name', 'last_name', 'receipt_email')

# -----------------------------
# Other Models
# -----------------------------
admin.site.register(PostLike)
admin.site.register(CommentLike)
admin.site.register(NoteLike)
admin.site.register(TextbookStockHistory)
admin.site.register(ContactMessage)

# -----------------------------
# Site Branding
# -----------------------------
admin.site.site_header = "EducAid Administration Panel"
admin.site.site_title = "EducAid Admin Portal"
admin.site.index_title = "Welcome to EducAid Admin Dashboard"