import re
from datetime import timedelta

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from MyNewApp import otp
from MyNewApp.models import EmailVerification

PASSWORD = 'Sunflower-Garden-42'


def _code_from_last_email():
    return re.search(r'\b(\d{6})\b', mail.outbox[-1].body).group(1)


class EmailOTPTests(TestCase):
    def register(self, **overrides):
        data = {
            'field_office': 'fo1', 'first_name': 'Maria', 'last_name': 'Santos',
            'username': 'maria', 'email': 'maria@example.com',
            'password': PASSWORD, 'confirm_password': PASSWORD,
        }
        data.update(overrides)
        return self.client.post(reverse('register'), data)

    def test_register_creates_inactive_user_and_emails_code(self):
        resp = self.register()
        self.assertRedirects(resp, reverse('verify_email'))
        user = User.objects.get(username='maria')
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['maria@example.com'])
        # Only a hash is stored, never the code itself
        self.assertNotIn(_code_from_last_email(), user.email_verification.code_hash)

    def test_correct_code_activates_and_logs_in(self):
        self.register()
        resp = self.client.post(reverse('verify_email'), {'code': _code_from_last_email()})
        self.assertRedirects(resp, reverse('dashboard'), fetch_redirect_response=False)
        user = User.objects.get(username='maria')
        self.assertTrue(user.is_active)
        self.assertFalse(EmailVerification.objects.filter(user=user).exists())
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_code_with_space_is_accepted(self):
        self.register()
        code = _code_from_last_email()
        self.client.post(reverse('verify_email'), {'code': f'{code[:3]} {code[3:]}'})
        self.assertTrue(User.objects.get(username='maria').is_active)

    def test_wrong_code_is_rejected_and_locks_after_max_attempts(self):
        self.register()
        right = _code_from_last_email()
        wrong = '000000' if right != '000000' else '111111'
        for _ in range(otp.MAX_ATTEMPTS):
            resp = self.client.post(reverse('verify_email'), {'code': wrong})
            self.assertEqual(resp.status_code, 200)
        # Even the right code fails once locked
        resp = self.client.post(reverse('verify_email'), {'code': right})
        self.assertContains(resp, 'Too many wrong tries')
        self.assertFalse(User.objects.get(username='maria').is_active)

    def test_expired_code_is_rejected(self):
        self.register()
        code = _code_from_last_email()
        EmailVerification.objects.update(created_at=EmailVerification.objects.get().created_at - otp.CODE_TTL - timedelta(seconds=1))
        resp = self.client.post(reverse('verify_email'), {'code': code})
        self.assertContains(resp, 'expired')
        self.assertFalse(User.objects.get(username='maria').is_active)

    def test_resend_respects_cooldown_and_replaces_code(self):
        self.register()
        self.client.post(reverse('resend_verification'))
        self.assertEqual(len(mail.outbox), 1)  # still in cooldown
        v = EmailVerification.objects.get()
        v.created_at -= otp.RESEND_COOLDOWN
        v.save()
        old_code = _code_from_last_email()
        self.client.post(reverse('resend_verification'))
        self.assertEqual(len(mail.outbox), 2)
        new_code = _code_from_last_email()
        if new_code != old_code:
            resp = self.client.post(reverse('verify_email'), {'code': old_code})
            self.assertContains(resp, 'That code isn')

    def test_login_before_verifying_sends_to_verify_page(self):
        self.register()
        self.client.logout()
        resp = self.client.post(reverse('index'), {'username': 'maria', 'password': PASSWORD})
        self.assertRedirects(resp, reverse('verify_email'))

    def test_login_with_wrong_password_does_not_reveal_unverified_account(self):
        self.register()
        resp = self.client.post(reverse('index'), {'username': 'maria', 'password': 'nope'})
        self.assertContains(resp, 'Incorrect username or password')

    def test_admin_disabled_account_is_not_offered_verification(self):
        User.objects.create_user('old', 'old@example.com', PASSWORD, is_active=False)
        resp = self.client.post(reverse('index'), {'username': 'old', 'password': PASSWORD})
        self.assertContains(resp, 'Incorrect username or password')

    def test_start_over_deletes_unverified_account(self):
        self.register()
        resp = self.client.post(reverse('cancel_verification'))
        self.assertRedirects(resp, reverse('register'))
        self.assertFalse(User.objects.filter(username='maria').exists())

    def test_verify_page_without_pending_signup_redirects_to_login(self):
        resp = self.client.get(reverse('verify_email'))
        self.assertRedirects(resp, reverse('index'))
