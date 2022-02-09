from django.contrib.auth import get_user_model
from django.test import TestCase, Client


User = get_user_model()


class UserURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='IsNotAuthor')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(
            UserURLTests.user)

    def test_guest_client_urls_uses_correct_template(self):
        """Проверка вызываемых шаблонов для signup, login"""
        templates_url_names = {
            '/auth/signup/': 'users/signup.html',
            '/auth/login/': 'users/login.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_authorized_client_urls_uses_correct_template(self):
        """Проверка вызываемых шаблонов для каждого адреса"""
        urls_templates_names = {
            '/auth/logout/': 'users/logged_out.html',
            '/auth/password_reset/': 'users/password_reset_form.html',
            '/auth/password_reset/done/': 'users/password_reset_done.html',
            '/auth/reset/hash/token/': 'users/password_reset_confirm.html',
            '/auth/reset/done/': 'users/password_reset_complete.html',
        }
        for url, template in urls_templates_names.items():
            with self.subTest(url=url, template=template):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_authorized_client_change_correct_template(self):
        """Проверка вызываемых шаблонов для каждого адреса
        изменения пароля
        """
        urls_templates_names = {
            '/auth/password_change/': 'users/password_change_form.html',
            '/auth/password_change/done/': 'users/password_change_done.html',
        }
        for url, template in urls_templates_names.items():
            with self.subTest(url=url, template=template):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
