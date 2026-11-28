from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from MyNewApp.models import Child, Attendance, Flag

class CDCCareTrackerTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testteacher',
            password='testpassword123',
            first_name='Ana',
            last_name='Santos'
        )
        self.client.force_login(self.user)

        self.child1 = Child.objects.create(
            user_id=self.user.id,
            first_name="Gabriel",
            last_name="Alvarez",
            date_of_birth=date(2020, 5, 15),
            gender="Male",
            address="Barangay 12, Caloocan"
        )
        self.child2 = Child.objects.create(
            user_id=self.user.id,
            first_name="Maria",
            last_name="Reyes",
            date_of_birth=date(2021, 8, 20),
            gender="Female",
            address="Poblacion, Curuan"
        )

    def test_dashboard_view(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gabriel Alvarez")
        self.assertContains(response, "Maria Reyes")

    def test_child_create_and_detail(self):
        response = self.client.post(reverse('child_record'), {
            'first_name': 'Juan',
            'last_name': 'Dela Cruz',
            'date_of_birth': '2019-01-10',
            'gender': 'Male',
            'address': 'Zone 4, Zamboanga'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Child.objects.filter(first_name='Juan').exists())

        new_child = Child.objects.get(first_name='Juan')
        detail_response = self.client.get(reverse('view_child', args=[new_child.id]))
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, "Juan Dela Cruz")

    def test_child_edit_and_delete(self):
        edit_response = self.client.post(reverse('edit_child', args=[self.child1.id]), {
            'first_name': 'Gabriel Updated',
            'last_name': 'Alvarez',
            'date_of_birth': '2020-05-15',
            'gender': 'Male',
            'address': 'Barangay 12, Caloocan'
        })
        self.assertEqual(edit_response.status_code, 302)
        self.child1.refresh_from_db()
        self.assertEqual(self.child1.first_name, 'Gabriel Updated')

        delete_response = self.client.post(reverse('delete_child', args=[self.child1.id]))
        self.assertEqual(delete_response.status_code, 302)
        self.assertFalse(Child.objects.filter(id=self.child1.id).exists())

    def test_attendance_workflow_today(self):
        today_str = timezone.localdate().strftime('%Y-%m-%d')
        response = self.client.post(reverse('attendance'), {
            'target_date': today_str,
            f'status_{self.child1.id}': 'Present',
            f'status_{self.child2.id}': 'Absent'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Attendance.objects.count(), 2)

        saved_response = self.client.get(reverse('attendance_saved'))
        self.assertEqual(saved_response.status_code, 200)
        self.assertContains(saved_response, "Attendance Recorded")

    def test_attendance_past_date_and_no_duplicates(self):
        past_date = timezone.localdate() - timedelta(days=5)
        past_date_str = past_date.strftime('%Y-%m-%d')

        # 1. Log attendance for a past date
        post1 = self.client.post(reverse('attendance'), {
            'target_date': past_date_str,
            f'status_{self.child1.id}': 'Present',
            f'status_{self.child2.id}': 'Present'
        })
        self.assertEqual(post1.status_code, 302)
        self.assertEqual(Attendance.objects.filter(date=past_date).count(), 2)

        # 2. View that past date's page (should load saved values)
        view_past = self.client.get(reverse('attendance') + f'?date={past_date_str}')
        self.assertEqual(view_past.status_code, 200)
        self.assertTrue(view_past.context['has_existing'])
        self.assertTrue(view_past.context['is_past'])

        # 3. Overwrite / update attendance for that same past date (e.g. child2 was actually Absent)
        post2 = self.client.post(reverse('attendance'), {
            'target_date': past_date_str,
            f'status_{self.child1.id}': 'Present',
            f'status_{self.child2.id}': 'Absent'
        })
        self.assertEqual(post2.status_code, 302)

        # Total records for that date MUST still be 2 (zero duplicates!)
        self.assertEqual(Attendance.objects.filter(date=past_date).count(), 2)
        att2 = Attendance.objects.get(child=self.child2, date=past_date)
        self.assertEqual(att2.status, 'Absent')

    def test_attendance_prevents_future_dates(self):
        tomorrow = timezone.localdate() + timedelta(days=1)
        tomorrow_str = tomorrow.strftime('%Y-%m-%d')

        # GET future date redirects/clamps
        get_future = self.client.get(reverse('attendance') + f'?date={tomorrow_str}')
        self.assertEqual(get_future.status_code, 302)

        # POST future date rejects
        post_future = self.client.post(reverse('attendance'), {
            'target_date': tomorrow_str,
            f'status_{self.child1.id}': 'Present',
            f'status_{self.child2.id}': 'Present'
        })
        self.assertEqual(post_future.status_code, 302)
        self.assertFalse(Attendance.objects.filter(date=tomorrow).exists())

    def test_flag_create_and_resolve_workflow(self):
        post_flag = self.client.post(reverse('add_flag'), {
            'child': self.child1.id,
            'flag_type': 'Absence streak',
            'note': 'Missed 3 consecutive days'
        })
        self.assertEqual(post_flag.status_code, 302)
        self.assertEqual(Flag.objects.filter(is_resolved=False).count(), 1)

        flag = Flag.objects.first()
        report_response = self.client.get(reverse('report'))
        self.assertEqual(report_response.status_code, 200)
        self.assertContains(report_response, "Absence streak")

        resolve_response = self.client.get(reverse('resolve_flag', args=[flag.id]))
        self.assertEqual(resolve_response.status_code, 302)
        flag.refresh_from_db()
        self.assertTrue(flag.is_resolved)
        self.assertEqual(Flag.objects.filter(is_resolved=False).count(), 0)

        # Verify child is marked in good standing once all flags are resolved
        self.assertFalse(self.child1.has_active_flags)
        dash_res = self.client.get(reverse('dashboard'))
        self.assertContains(dash_res, "OK")
        dir_res = self.client.get(reverse('child_record'))
        self.assertContains(dir_res, "Good")
        detail_res = self.client.get(reverse('view_child', args=[self.child1.id]))
        self.assertContains(detail_res, "In Good Standing")

    def test_flag_resolve_ajax_endpoint(self):
        flag = Flag.objects.create(
            child=self.child1,
            flag_type='Behavioral note',
            note='Needs observation during nap time'
        )
        # Verify initial child record page shows the flag
        detail_res = self.client.get(reverse('view_child', args=[self.child1.id]))
        self.assertEqual(detail_res.status_code, 200)
        self.assertContains(detail_res, 'id="resolveModal"')
        self.assertContains(detail_res, 'Behavioral note')
        self.assertContains(detail_res, 'btn-resolve-trigger')

        # Send AJAX resolve request
        ajax_res = self.client.post(
            reverse('resolve_flag', args=[flag.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(ajax_res.status_code, 200)
        json_data = ajax_res.json()
        self.assertEqual(json_data['status'], 'success')
        self.assertEqual(json_data['flag_id'], flag.id)
        self.assertEqual(json_data['remaining_child_flags'], 0)

        flag.refresh_from_db()
        self.assertTrue(flag.is_resolved)

    def test_search_view(self):
        response = self.client.get(reverse('search') + '?q=Maria')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Maria Reyes')

    def test_export_attendance_excel(self):
        # Create an attendance entry
        today = timezone.localdate()
        Attendance.objects.create(child=self.child1, date=today, status='Present')

        response = self.client.get(reverse('export_attendance_excel') + f'?year={today.year}&month={today.month}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertTrue('attachment;' in response['Content-Disposition'])
        self.assertTrue('.xlsx' in response['Content-Disposition'])
        self.assertGreater(len(response.content), 1000)

    def test_export_attendance_pdf(self):
        today = timezone.localdate()
        Attendance.objects.create(child=self.child1, date=today, status='Present')

        response = self.client.get(reverse('export_attendance_pdf') + f'?year={today.year}&month={today.month}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue('attachment;' in response['Content-Disposition'])
        self.assertTrue('.pdf' in response['Content-Disposition'])
        self.assertGreater(len(response.content), 1000)

    def test_attendance_monthly_preview(self):
        today = timezone.localdate()
        response = self.client.get(reverse('attendance_monthly_preview') + f'?year={today.year}&month={today.month}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Child Development Center")
        self.assertContains(response, "Gabriel")
        self.assertContains(response, "Maria")

    def test_register_page_loads(self):
        self.client.logout()
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create account")
        self.assertContains(response, "First name")
        self.assertContains(response, "Last name")
        self.assertContains(response, "Username")
        self.assertContains(response, "Email address")
        self.assertContains(response, "Log in")

    def test_register_authenticated_user_redirect(self):
        # Already logged in via setUp
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_register_successful_creation(self):
        self.client.logout()
        post_data = {
            'field_office': 'fo1',
            'first_name': 'Teresa',
            'last_name': 'Mendoza',
            'username': 'teresam',
            'email': 'teresa.mendoza@example.com',
            'password': 'StrongPassword2026!',
            'confirm_password': 'StrongPassword2026!',
        }
        response = self.client.post(reverse('register'), post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('verify_email'))

        # Verify user in database (inactive until email OTP verified)
        user = User.objects.get(username='teresam')
        self.assertEqual(user.first_name, 'Teresa')
        self.assertEqual(user.last_name, 'Mendoza')
        self.assertEqual(user.email, 'teresa.mendoza@example.com')
        self.assertTrue(user.check_password('StrongPassword2026!'))
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

        # Verify pending verification session
        self.assertEqual(self.client.session['verify_user_id'], user.id)

    def test_register_duplicate_username(self):
        self.client.logout()
        post_data = {
            'first_name': 'Duplicate',
            'last_name': 'User',
            'username': 'testteacher',  # Already created in setUp
            'email': 'newemail@example.com',
            'password': 'StrongPassword2026!',
            'confirm_password': 'StrongPassword2026!',
        }
        response = self.client.post(reverse('register'), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This username is already taken. Please choose another.")
        self.assertFalse(User.objects.filter(email='newemail@example.com').exists())

    def test_register_duplicate_email(self):
        self.client.logout()
        # Set email on existing user
        self.user.email = 'teacher@example.com'
        self.user.save()

        post_data = {
            'first_name': 'Duplicate',
            'last_name': 'Email',
            'username': 'differentuser',
            'email': 'TEACHER@example.com',  # case-insensitive check
            'password': 'StrongPassword2026!',
            'confirm_password': 'StrongPassword2026!',
        }
        response = self.client.post(reverse('register'), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "An account with this email address already exists.")
        self.assertFalse(User.objects.filter(username='differentuser').exists())

    def test_register_password_mismatch(self):
        self.client.logout()
        post_data = {
            'first_name': 'Carlos',
            'last_name': 'Garcia',
            'username': 'carlosg',
            'email': 'carlos@example.com',
            'password': 'StrongPassword2026!',
            'confirm_password': 'DifferentPassword2026!',
        }
        response = self.client.post(reverse('register'), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Passwords do not match.")
        self.assertFalse(User.objects.filter(username='carlosg').exists())

    def test_register_weak_password(self):
        self.client.logout()
        post_data = {
            'first_name': 'Carlos',
            'last_name': 'Garcia',
            'username': 'carlosg2',
            'email': 'carlos2@example.com',
            'password': '123',
            'confirm_password': '123',
        }
        response = self.client.post(reverse('register'), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='carlosg2').exists())
