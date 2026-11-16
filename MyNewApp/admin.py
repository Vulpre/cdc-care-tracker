from django.contrib import admin
# pyrefly: ignore [missing-import]
from MyNewApp.models import Child, AboutMe, MyModel, TestModel, Attendance, Flag

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



