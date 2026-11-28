from datetime import date, datetime, timedelta
import calendar
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from MyNewApp.models import Child, AboutMe, Attendance, Flag, EmailVerification
from MyNewApp.forms import ChildForm, RegistrationForm
from MyNewApp import otp
from MyNewApp.db_router import set_db_alias
from MyNewApp.reports import (
    get_monthly_attendance_data,
    generate_attendance_excel,
    generate_attendance_pdf
)


def _apply_field_office_db(request):
    """Set the thread-local DB alias from the logged-in user's field office."""
    if request.user.is_authenticated:
        try:
            set_db_alias(request.user.profile.db_alias)
        except Exception:
            set_db_alias('default')


# ── LOGIN / LOGOUT / PASSWORD RESET ──────────────────────────

def index(request):
    """Login page. Redirect to dashboard if already logged in."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    error = None
    username = ''

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username:
            error = 'Please enter your username or email.'
        elif not password:
            error = 'Please enter your password.'
        else:
            # Allow logging in with either username or email
            login_username = username
            if '@' in username:
                matched_user = User.objects.filter(email__iexact=username).first()
                if matched_user:
                    login_username = matched_user.username
            else:
                matched_user = User.objects.filter(username__iexact=username).first()
                if matched_user:
                    login_username = matched_user.username

            user = authenticate(request, username=login_username, password=password)
            if user is not None:
                login(request, user)
                # Honour ?next= param if present
                next_url = request.GET.get('next', '/dashboard/')
                return redirect(next_url)
            elif _is_unverified(matched_user) and matched_user.check_password(password):
                # Signed up but never entered the emailed code: send a fresh one.
                if otp.seconds_until_resend(matched_user) == 0:
                    otp.send_code(matched_user)
                request.session[VERIFY_SESSION_KEY] = matched_user.pk
                return redirect('verify_email')
            else:
                error = 'Incorrect username or password. Please try again.'

    return render(request, 'index.html', {'error': error, 'username': username})


def register_view(request):
    """Sign up / Create account view. Registers a new teacher/staff user."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Account starts inactive until the emailed code is entered.
            user = form.save()
            otp.send_code(user)
            request.session[VERIFY_SESSION_KEY] = user.pk
            return redirect('verify_email')
    else:
        form = RegistrationForm()

    return render(request, 'register.html', {'form': form})


# ── EMAIL VERIFICATION (OTP) ─────────────────────────────────

VERIFY_SESSION_KEY = 'verify_user_id'


def _is_unverified(user):
    """Inactive *and* has a pending code. Admin-disabled accounts have no code row."""
    return (user is not None and not user.is_active
            and EmailVerification.objects.filter(user=user).exists())


def _pending_user(request):
    user = User.objects.filter(pk=request.session.get(VERIFY_SESSION_KEY)).first()
    return user if _is_unverified(user) else None


def verify_email(request):
    """Enter the 6-digit code sent after sign-up."""
    user = _pending_user(request)
    if user is None:
        request.session.pop(VERIFY_SESSION_KEY, None)
        return redirect('index')

    error = None
    if request.method == 'POST':
        code = ''.join(ch for ch in request.POST.get('code', '') if ch.isdigit())
        if len(code) != 6:
            error = 'Enter the 6-digit code from the email.'
        else:
            result = otp.check_code(user, code)
            if result == otp.OK:
                request.session.pop(VERIFY_SESSION_KEY, None)
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, f"Welcome to CDC Care Tracker, {user.first_name}! Your email is verified and your account is ready.")
                return redirect('dashboard')
            error = {
                otp.WRONG:    "That code isn't right. Check the email and try again.",
                otp.EXPIRED:  'That code has expired. Send a new code below.',
                otp.TOO_MANY: 'Too many wrong tries. Send a new code below.',
                otp.MISSING:  'Send a new code below.',
            }[result]

    return render(request, 'verify-email.html', {
        'error': error,
        'masked_email': otp.mask_email(user.email),
        'resend_in': otp.seconds_until_resend(user),
        'ttl_minutes': int(otp.CODE_TTL.total_seconds() // 60),
    })


def resend_verification(request):
    """POST only: email a new code, at most once per cooldown."""
    user = _pending_user(request)
    if user is None:
        return redirect('index')
    if request.method == 'POST':
        if otp.seconds_until_resend(user) == 0:
            otp.send_code(user)
            messages.success(request, 'A new code is on its way.')
    return redirect('verify_email')


def cancel_verification(request):
    """POST only: discard the unverified sign-up so the person can register again."""
    user = _pending_user(request)
    if user is not None and request.method == 'POST':
        user.delete()  # cascades to UserProfile and EmailVerification
        request.session.pop(VERIFY_SESSION_KEY, None)
        return redirect('register')
    return redirect('verify_email' if user else 'index')


def logout_view(request):
    """Log the user out and redirect to the login page."""
    logout(request)
    return redirect('index')


def password_reset_request(request):
    """Send a password-reset e-mail (prints to console in dev)."""
    sent = False
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                token_generator=default_token_generator,
                email_template_name='registration/password_reset_email.html',
            )
            sent = True
    else:
        form = PasswordResetForm()
    return render(request, 'password-reset.html', {'form': form, 'sent': sent})


# ── ALL VIEWS BELOW REQUIRE LOGIN ─────────────────────────────

@login_required
def select_cdc(request):
    return render(request, 'select-cdc.html')

@login_required
def dashboard(request):
    _apply_field_office_db(request)
    today = timezone.localdate()

    # Summary stats
    total_children   = Child.objects.count()
    present_today    = Attendance.objects.filter(date=today, status='Present').count()
    absent_today     = Attendance.objects.filter(date=today, status='Absent').count()
    unresolved_flags = Flag.objects.filter(is_resolved=False).count()

    # Recent children (last 5 added)
    children = Child.objects.all().order_by('-id')[:5]

    # Recent flags (latest 5 unresolved)
    recent_flags = Flag.objects.filter(is_resolved=False).select_related('child').order_by('-created_at')[:5]

    # Recent attendance activity (last 5 records)
    recent_attendance = Attendance.objects.select_related('child').order_by('-created_at')[:5]

    # Attendance chart data: last 7 days present/absent counts
    chart_labels = []
    chart_present = []
    chart_absent  = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        chart_labels.append(day.strftime('%b %d'))
        chart_present.append(Attendance.objects.filter(date=day, status='Present').count())
        chart_absent.append(Attendance.objects.filter(date=day, status='Absent').count())

    # Field office label
    field_office_label = ''
    try:
        field_office_label = request.user.profile.get_field_office_display()
    except Exception:
        pass

    return render(request, 'dashboard.html', {
        'today':             today,
        'total_children':    total_children,
        'present_today':     present_today,
        'absent_today':      absent_today,
        'unresolved_flags':  unresolved_flags,
        'children':          children,
        'recent_flags':      recent_flags,
        'recent_attendance': recent_attendance,
        'chart_labels':      chart_labels,
        'chart_present':     chart_present,
        'chart_absent':      chart_absent,
        'field_office_label': field_office_label,
    })

@login_required
def attendance(request):
    _apply_field_office_db(request)
    children = Child.objects.all().order_by('last_name', 'first_name')
    unresolved_flags = Flag.objects.filter(is_resolved=False).count()
    today = timezone.localdate()

    # Parse and validate target date from POST or GET
    if request.method == 'POST':
        date_str = request.POST.get('target_date', '').strip() or request.GET.get('date', '').strip()
    else:
        date_str = request.GET.get('date', '').strip()

    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Invalid date format. Showing today instead.')
            target_date = today
    else:
        target_date = today

    # Prevent future dates
    if target_date > today:
        messages.warning(request, f'Attendance cannot be recorded for future dates. Displaying today ({today.strftime("%b %d, %Y")}).')
        return redirect(f'/attendance/?date={today.strftime("%Y-%m-%d")}')

    is_today = (target_date == today)
    is_past = (target_date < today)
    prev_date = target_date - timedelta(days=1)
    next_date = (target_date + timedelta(days=1)) if target_date < today else None

    if request.method == 'POST':
        present_count = 0
        absent_count = 0
        for child in children:
            status = request.POST.get(f'status_{child.id}', 'Present')
            Attendance.objects.update_or_create(
                child=child,
                date=target_date,
                defaults={'status': status}
            )
            if status == 'Present':
                present_count += 1
            else:
                absent_count += 1

        request.session['att_date'] = target_date.strftime('%Y-%m-%d')
        request.session['att_present'] = present_count
        request.session['att_absent'] = absent_count
        return redirect('attendance_saved')

    # GET: Check existing records for target_date
    existing_recs = Attendance.objects.filter(date=target_date)
    att_map = {rec.child_id: rec.status for rec in existing_recs}
    has_existing = bool(existing_recs.exists())

    child_statuses = []
    present_tally = 0
    absent_tally = 0
    for child in children:
        st = att_map.get(child.id, 'Present')
        if st == 'Present':
            present_tally += 1
        else:
            absent_tally += 1
        child_statuses.append({
            'child': child,
            'status': st,
        })

    return render(request, 'attendance.html', {
        'children': children,
        'child_statuses': child_statuses,
        'target_date': target_date,
        'today': today,
        'is_today': is_today,
        'is_past': is_past,
        'prev_date': prev_date,
        'next_date': next_date,
        'has_existing': has_existing,
        'present_tally': present_tally,
        'absent_tally': absent_tally,
        'unresolved_flags': unresolved_flags,
    })

@login_required
def attendance_saved(request):
    present = request.session.get('att_present', 0)
    absent  = request.session.get('att_absent', 0)
    date_str = request.session.get('att_date')
    saved_date = None
    if date_str:
        try:
            saved_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    return render(request, 'attendance-saved.html', {
        'present': present,
        'absent': absent,
        'saved_date': saved_date,
    })

# ── FULL CRUD: CHILD ──────────────────────────────────────────

@login_required
def child_record(request):
    _apply_field_office_db(request)
    children = Child.objects.all()
    unresolved_flags = Flag.objects.filter(is_resolved=False).count()
    form = ChildForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Child record saved successfully.')
        return redirect('child_record')
    return render(request, 'child-record.html', {
        'children': children,
        'form': form,
        'unresolved_flags': unresolved_flags,
    })

@login_required
def view_child(request, id):
    child = get_object_or_404(Child, id=id)
    attendances = child.attendances.order_by('-date')[:5]
    flags = child.flags.order_by('-created_at')
    active_flags = child.flags.filter(is_resolved=False).order_by('-created_at')
    resolved_flags = child.flags.filter(is_resolved=True).order_by('-created_at')
    unresolved_flags = Flag.objects.filter(is_resolved=False).count()
    return render(request, 'record-detail.html', {
        'child': child,
        'attendances': attendances,
        'flags': flags,
        'active_flags': active_flags,
        'resolved_flags': resolved_flags,
        'has_active_flags': active_flags.exists(),
        'unresolved_flags': unresolved_flags,
    })

@login_required
def edit_child(request, id):
    child = get_object_or_404(Child, id=id)
    form = ChildForm(request.POST or None, instance=child)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Child record updated.')
        return redirect('view_child', id=child.id)
    return render(request, 'edit-child.html', {'child': child, 'form': form})

@login_required
def delete_child(request, id):
    child = get_object_or_404(Child, id=id)
    if request.method == 'POST':
        child.delete()
        messages.success(request, 'Record deleted.')
        return redirect('child_record')
    return render(request, 'delete-child.html', {'child': child})

# ─────────────────────────────────────────────────────────────

@login_required
def record_detail(request):
    first_child = Child.objects.first()
    if first_child:
        return redirect('view_child', id=first_child.id)
    return redirect('child_record')

@login_required
def add_flag(request):
    children = Child.objects.all()
    unresolved_flags = Flag.objects.filter(is_resolved=False).count()
    if request.method == 'POST':
        child_id  = request.POST.get('child')
        flag_type = request.POST.get('flag_type', 'Absence streak')
        note      = request.POST.get('note', '')
        if child_id:
            child = get_object_or_404(Child, id=child_id)
            flag  = Flag.objects.create(child=child, flag_type=flag_type, note=note)
            request.session['last_flag_child'] = f"{child.first_name} {child.last_name}"
            request.session['last_flag_type']  = flag.flag_type
            return redirect('flag_saved')
    return render(request, 'add-flag.html', {'children': children, 'unresolved_flags': unresolved_flags})

@login_required
def resolve_flag(request, id):
    flag = get_object_or_404(Flag, id=id)
    flag.is_resolved = True
    flag.save()
    messages.success(request, f"Flag '{flag.flag_type}' for {flag.child.first_name} {flag.child.last_name} marked as resolved.")

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
        child = flag.child
        remaining_child_flags = child.flags.filter(is_resolved=False).count()
        total_unresolved = Flag.objects.filter(is_resolved=False).count()
        return JsonResponse({
            'status': 'success',
            'message': f"Flag '{flag.flag_type}' has been resolved.",
            'flag_id': flag.id,
            'child_id': child.id,
            'child_name': f"{child.first_name} {child.last_name}",
            'remaining_child_flags': remaining_child_flags,
            'total_unresolved': total_unresolved,
        })

    referer = request.META.get('HTTP_REFERER')
    if referer and 'http' in referer:
        return redirect(referer)
    return redirect('view_child', id=flag.child.id)

@login_required
def flag_saved(request):
    child_name = request.session.get('last_flag_child', 'Child Record')
    flag_type  = request.session.get('last_flag_type', 'Flag')
    return render(request, 'flag-saved.html', {'child_name': child_name, 'flag_type': flag_type})

@login_required
def profile(request):
    profile_data = AboutMe.objects.first()
    field_office_label = ''
    try:
        field_office_label = request.user.profile.get_field_office_display()
    except Exception:
        pass
    return render(request, 'profile.html', {
        'profile': profile_data,
        'field_office_label': field_office_label,
    })

@login_required
def desk_profile(request):
    return redirect('profile')

@login_required
def search(request):
    _apply_field_office_db(request)
    query = request.GET.get('q', '').strip()
    if query:
        children = Child.objects.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(barangay__icontains=query)
            | Q(address__icontains=query)
        ).prefetch_related('flags')
    else:
        children = Child.objects.all().prefetch_related('flags')
    return render(request, 'search.html', {'children': children, 'query': query})

@login_required
def report(request):
    _apply_field_office_db(request)
    total_children = Child.objects.count()
    unresolved_flags = Flag.objects.filter(is_resolved=False).count()
    total_attendances = Attendance.objects.count()
    flags = Flag.objects.select_related('child').all()

    # Reporting options
    today = timezone.localdate()
    curr_year = today.year
    curr_month = today.month

    try:
        selected_year = int(request.GET.get('year', curr_year))
        selected_month = int(request.GET.get('month', curr_month))
        if not (1 <= selected_month <= 12):
            selected_month = curr_month
    except (TypeError, ValueError):
        selected_year = curr_year
        selected_month = curr_month

    months_list = [
        {'num': m, 'name': calendar.month_name[m]}
        for m in range(1, 13)
    ]
    years_list = list(range(curr_year - 2, curr_year + 1))

    return render(request, 'report.html', {
        'total_children': total_children,
        'unresolved_flags': unresolved_flags,
        'total_attendances': total_attendances,
        'flags': flags,
        'months_list': months_list,
        'years_list': years_list,
        'selected_year': selected_year,
        'selected_month': selected_month,
        'selected_month_name': calendar.month_name[selected_month],
    })


@login_required
def export_attendance_excel(request):
    """Generates and downloads a monthly attendance Excel (.xlsx) file."""
    now = timezone.localdate()
    try:
        year = int(request.GET.get('year', now.year))
        month = int(request.GET.get('month', now.month))
        if not (1 <= month <= 12):
            month = now.month
    except (TypeError, ValueError):
        year = now.year
        month = now.month

    data = get_monthly_attendance_data(year, month)
    user_name = request.user.get_full_name() or request.user.username
    buf = generate_attendance_excel(data, center_name="Child Development Center", user_name=user_name)

    filename = f"CDC_Attendance_{data['month_name']}_{year}.xlsx"
    response = HttpResponse(
        buf.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def export_attendance_pdf(request):
    """Generates and downloads a monthly attendance PDF file."""
    now = timezone.localdate()
    try:
        year = int(request.GET.get('year', now.year))
        month = int(request.GET.get('month', now.month))
        if not (1 <= month <= 12):
            month = now.month
    except (TypeError, ValueError):
        year = now.year
        month = now.month

    data = get_monthly_attendance_data(year, month)
    user_name = request.user.get_full_name() or request.user.username
    buf = generate_attendance_pdf(data, center_name="Child Development Center", user_name=user_name)

    filename = f"CDC_Attendance_{data['month_name']}_{year}.pdf"
    response = HttpResponse(buf.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def attendance_monthly_preview(request):
    """Renders a full print-ready HTML monthly attendance sheet with print controls."""
    now = timezone.localdate()
    try:
        year = int(request.GET.get('year', now.year))
        month = int(request.GET.get('month', now.month))
        if not (1 <= month <= 12):
            month = now.month
    except (TypeError, ValueError):
        year = now.year
        month = now.month

    data = get_monthly_attendance_data(year, month)
    user_name = request.user.get_full_name() or request.user.username
    unresolved_flags = Flag.objects.filter(is_resolved=False).count()

    months_list = [{'num': m, 'name': calendar.month_name[m]} for m in range(1, 13)]
    years_list = list(range(now.year - 2, now.year + 1))

    return render(request, 'attendance-monthly-preview.html', {
        'data': data,
        'year': year,
        'month': month,
        'user_name': user_name,
        'unresolved_flags': unresolved_flags,
        'months_list': months_list,
        'years_list': years_list,
    })



