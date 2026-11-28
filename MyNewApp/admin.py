from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
# pyrefly: ignore [missing-import]
from MyNewApp.models import Child, AboutMe, MyModel, TestModel, Attendance, Flag, UserProfile


# ── UserProfile inline — shown inside the User edit page ─────
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = 'Field Office Assignment'
    verbose_name_plural = 'Field Office Assignment'
    fields = ('field_office',)


# ── Extended User admin ───────────────────────────────────────
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display  = ('username', 'email', 'first_name', 'last_name', 'get_field_office', 'is_staff', 'is_active')
    list_filter   = ('is_staff', 'is_superuser', 'is_active', 'profile__field_office')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'profile__field_office')

    @admin.display(description='Field Office')
    def get_field_office(self, obj):
        try:
            return obj.profile.get_field_office_display()
        except UserProfile.DoesNotExist:
            return '—'


# Unregister the default User admin and register the extended one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# ── UserProfile standalone admin ─────────────────────────────
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display  = ('user', 'get_full_name', 'field_office')
    list_filter   = ('field_office',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email')
    autocomplete_fields = ('user',)

    @admin.display(description='Full Name')
    def get_full_name(self, obj):
        return obj.user.get_full_name() or '—'



@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'date_of_birth', 'gender')
    search_fields = ('first_name', 'last_name')

@admin.register(AboutMe)
class AboutMeAdmin(admin.ModelAdmin):
    list_display  = ('full_name', 'initials', 'course', 'year_section', 'role', 'updated_at')
    search_fields = ('full_name',)
    fieldsets = (
        ('Personal Info', {
            'fields': ('full_name', 'initials', 'course', 'year_section', 'role')
        }),
        ('Content', {
            'fields': ('bio', 'skills')
        }),
    )

@admin.register(MyModel)
class MyModelAdmin(admin.ModelAdmin):
    list_display  = ('name', 'age', 'email', 'phone_number', 'created_at')
    search_fields = ('name', 'email', 'phone_number')

@admin.register(TestModel)
class TestModelAdmin(admin.ModelAdmin):
    list_display  = ('title', 'number', 'is_active', 'created_at')
    search_fields = ('title',)
    list_filter   = ('is_active',)



@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display  = ('child', 'date', 'status', 'created_at')
    search_fields = ('child__first_name', 'child__last_name')
    list_filter   = ('status', 'date')

@admin.register(Flag)
class FlagAdmin(admin.ModelAdmin):
    list_display  = ('child', 'flag_type', 'is_resolved', 'created_at')
    search_fields = ('child__first_name', 'child__last_name', 'note')
    list_filter   = ('flag_type', 'is_resolved')



