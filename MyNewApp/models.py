from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# ── Field Office ─────────────────────────────────────────────
FIELD_OFFICE_CHOICES = [
    ('fo1', 'Field Office 1 — Ayala District'),
    ('fo2', 'Field Office 2 — Sta. Barbara District'),
    ('fo3', 'Field Office 3 — Sta. Maria District'),
    ('fo4', 'Field Office 4 — Tetuan District'),
    ('fo5', 'Field Office 5 — Culianan District'),
    ('fo6', 'Field Office 6 — Curuan District'),
    ('fo7', 'Field Office 7 — Vitali District'),
]

# Maps field office key → database alias used in settings.py
FIELD_OFFICE_DB_MAP = {
    'fo1': 'fo1_db',
    'fo2': 'fo2_db',
    'fo3': 'fo3_db',
    'fo4': 'fo4_db',
    'fo5': 'fo5_db',
    'fo6': 'fo6_db',
    'fo7': 'fo7_db',
}


class UserProfile(models.Model):
    """Extends the built-in User with a Field Office assignment."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    field_office = models.CharField(
        max_length=10,
        choices=FIELD_OFFICE_CHOICES,
        default='fo1',
        verbose_name='Field Office',
    )

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username} — {self.get_field_office_display()}"

    @property
    def db_alias(self):
        """Returns the database alias this user's children data lives in."""
        return FIELD_OFFICE_DB_MAP.get(self.field_office, 'default')


# ── Child Model ──────────────────────────────────────────────
class Child(models.Model):
    user_id       = models.IntegerField(null=True, blank=True, db_index=True)
    first_name    = models.CharField(max_length=100)
    last_name     = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender        = models.CharField(max_length=10)
    weight_kg     = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Weight (kg)")
    height_cm     = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Height (cm)")
    nutritional_status = models.CharField(max_length=50, blank=True, default='', verbose_name="Nutritional Status")
    barangay      = models.CharField(max_length=100, blank=True, default='')
    address       = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def has_active_flags(self):
        """Returns True only if the child has unresolved active flags."""
        return any(not f.is_resolved for f in self.flags.all())

    @property
    def active_flags_list(self):
        """Returns only unresolved active flags for this child."""
        return [f for f in self.flags.all() if not f.is_resolved]

    @property
    def active_flags_count(self):
        """Count of active unresolved flags."""
        return sum(1 for f in self.flags.all() if not f.is_resolved)


# ── Attendance Record Model ──────────────────────────────────
class Attendance(models.Model):
    child      = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='attendances')
    date       = models.DateField(default=timezone.localdate)
    status     = models.CharField(max_length=10, choices=[('Present', 'Present'), ('Absent', 'Absent')], default='Present')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Attendance"
        verbose_name_plural = "Attendances"
        unique_together     = ('child', 'date')

    def __str__(self):
        return f"{self.child} - {self.date}: {self.status}"


# ── Flag / Alert Model ───────────────────────────────────────
class Flag(models.Model):
    FLAG_CHOICES = [
        ('Absence streak', 'Absence streak'),
        ('Underweight', 'Underweight'),
        ('Illness', 'Illness'),
        ('Behavioral', 'Behavioral'),
    ]
    child       = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='flags')
    flag_type   = models.CharField(max_length=50, choices=FLAG_CHOICES, default='Absence streak')
    note        = models.TextField(blank=True)
    is_resolved = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Flag"
        verbose_name_plural = "Flags"

    def __str__(self):
        return f"{self.flag_type} - {self.child}"


# ── About Me model ───────────────────────────────────────────
class AboutMe(models.Model):
    full_name    = models.CharField(max_length=150, verbose_name="Full Name")
    initials     = models.CharField(max_length=5, verbose_name="Avatar Initials",
                                    help_text="e.g. AZ — shown on the avatar circle")
    course       = models.CharField(max_length=150, verbose_name="Course",
                                    default="BS Information Technology")
    year_section = models.CharField(max_length=50, verbose_name="Year & Section",
                                    default="3rd Year — IT3A")
    role         = models.CharField(max_length=100, verbose_name="Role",
                                    default="Student Developer")
    bio          = models.TextField(verbose_name="About / Bio", blank=True)
    skills       = models.TextField(verbose_name="Skills (comma-separated)", blank=True,
                                    help_text="e.g. Python, Django, HTML & CSS, JavaScript")
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "About Me"
        verbose_name_plural = "About Me"

    def __str__(self):
        return self.full_name

    def skills_list(self):
        return [s.strip() for s in self.skills.split(',') if s.strip()]


# ── MyModel (lab exercise) ───────────────────────────────────
class MyModel(models.Model):
    name         = models.CharField(max_length=100, verbose_name="Name")
    description  = models.TextField(verbose_name="Description", blank=True)
    age          = models.IntegerField(verbose_name="Age", default=0)
    email        = models.EmailField(verbose_name="Email", blank=True)
    phone_number = models.CharField(max_length=15, verbose_name="Phone Number", blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "My Model"
        verbose_name_plural = "My Models"

    def __str__(self):
        return self.name


# ── Test Model ───────────────────────────────────────────────
class TestModel(models.Model):
    title       = models.CharField(max_length=100, verbose_name="Title")
    number      = models.IntegerField(verbose_name="Number", default=0)
    is_active   = models.BooleanField(verbose_name="Is Active", default=True)
    notes       = models.TextField(verbose_name="Notes", blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Test Model"
        verbose_name_plural = "Test Models"

    def __str__(self):
        return self.title


