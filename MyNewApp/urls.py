from django.urls import path, reverse_lazy
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from MyNewApp import views

urlpatterns = [
    # Auth
    path('', views.index, name='index'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Password reset
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='password-reset-done.html'),
         name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='password-reset-confirm.html',
             success_url=reverse_lazy('password_reset_complete'),
         ),
         name='password_reset_confirm'),
    path('password-reset/complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='password-reset-complete.html'),
         name='password_reset_complete'),

    # App
    path('about-me/', views.about_me, name='about_me'),
    path('about_me', RedirectView.as_view(url='/about-me/')),
    path('select-cdc/', views.select_cdc, name='select_cdc'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('attendance/', views.attendance, name='attendance'),
    path('attendance-saved/', views.attendance_saved, name='attendance_saved'),
    path('child-record/', views.child_record, name='child_record'),
    path('child/<int:id>/', views.view_child, name='view_child'),
    path('child/<int:id>/edit/', views.edit_child, name='edit_child'),
    path('child/<int:id>/delete/', views.delete_child, name='delete_child'),
    path('record-detail/', views.record_detail, name='record_detail'),
    path('add-flag/', views.add_flag, name='add_flag'),
    path('flag-saved/', views.flag_saved, name='flag_saved'),
    path('flag/<int:id>/resolve/', views.resolve_flag, name='resolve_flag'),
    path('profile/', views.profile, name='profile'),
    path('desk-profile/', views.desk_profile, name='desk_profile'),
    path('search/', views.search, name='search'),
    path('report/', views.report, name='report'),
    path('report/attendance/excel/', views.export_attendance_excel, name='export_attendance_excel'),
    path('report/attendance/pdf/', views.export_attendance_pdf, name='export_attendance_pdf'),
    path('report/attendance/preview/', views.attendance_monthly_preview, name='attendance_monthly_preview'),
]
