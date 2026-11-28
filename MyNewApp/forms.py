import re
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from MyNewApp.models import Child, AboutMe, MyModel, Flag, FIELD_OFFICE_CHOICES


class RegistrationForm(forms.Form):
    field_office = forms.ChoiceField(
        choices=FIELD_OFFICE_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'input',
        }),
        label='Field Office',
    )
    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'input',
            'placeholder': 'First Name',
            'autocomplete': 'given-name',
            'autofocus': 'autofocus'
        })
    )
    last_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'input',
            'placeholder': 'Last Name',
            'autocomplete': 'family-name'
        })
    )
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'input',
            'placeholder': 'Choose a username',
            'autocomplete': 'username'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'input',
            'placeholder': 'name@example.com',
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'input',
            'placeholder': 'Create a password',
            'autocomplete': 'new-password'
        })
    )
    confirm_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'input',
            'placeholder': 'Re-enter password',
            'autocomplete': 'new-password'
        })
    )

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name', '').strip()
        if len(first_name) < 2:
            raise ValidationError('First name must be at least 2 characters.')
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name', '').strip()
        if len(last_name) < 2:
            raise ValidationError('Last name must be at least 2 characters.')
        return last_name

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if not re.match(r'^[\w.@+-]+$', username):
            raise ValidationError('Username can only contain letters, numbers, and @/./+/-/_ characters.')
        if len(username) < 3:
            raise ValidationError('Username must be at least 3 characters long.')
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('This username is already taken. Please choose another.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email address already exists.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password:
            if password != confirm_password:
                self.add_error('confirm_password', 'Passwords do not match.')
            else:
                username = cleaned_data.get('username', '')
                user = User(username=username, email=cleaned_data.get('email', ''))
                try:
                    validate_password(password, user=user)
                except ValidationError as e:
                    self.add_error('password', e)

        return cleaned_data

    def save(self):
        cleaned_data = self.cleaned_data
        user = User.objects.create_user(
            username=cleaned_data['username'],
            email=cleaned_data['email'],
            password=cleaned_data['password'],
            first_name=cleaned_data['first_name'],
            last_name=cleaned_data['last_name'],
            is_staff=False,
            is_superuser=False,
            is_active=False,  # activated after the emailed code is verified (see otp.py)
        )
        # Create the UserProfile with the chosen field office
        from MyNewApp.models import UserProfile
        UserProfile.objects.create(
            user=user,
            field_office=cleaned_data['field_office'],
        )
        return user


class ChildForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = '__all__'
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }


class FlagForm(forms.ModelForm):
    class Meta:
        model = Flag
        fields = ['child', 'flag_type', 'note']
        widgets = {
            'child': forms.Select(attrs={'class': 'input'}),
            'flag_type': forms.Select(attrs={'class': 'input'}),
            'note': forms.Textarea(attrs={'class': 'textarea', 'placeholder': 'What did you notice?'}),
        }

class AboutMeForm(forms.ModelForm):
    class Meta:
        model = AboutMe
        fields = ['full_name', 'initials', 'course', 'year_section', 'role', 'bio', 'skills']

class MyModelForm(forms.ModelForm):
    class Meta:
        model = MyModel
        fields = '__all__'

