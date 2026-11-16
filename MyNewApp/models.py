from django.db import models
from django.utils import timezone


# ── Child Model ──────────────────────────────────────────────
class Child(models.Model):
    first_name    = models.CharField(max_length=100)
    last_name     = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender        = models.CharField(max_length=10)
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


