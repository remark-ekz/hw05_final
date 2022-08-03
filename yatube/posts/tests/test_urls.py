from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.core.cache import cache
from http import HTTPStatus

from posts.models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=PostURLTests.user,
            text='Тестовый пост',
            id='1',
            group=PostURLTests.group,
        )
        cls.post_edit = f'/posts/{cls.post.id}/edit/'
        cls.post_create = '/create/'
        cls.post_url = f'/posts/{cls.post.id}/'
        cls.public_urls = (
            ('/', 'posts/index.html'),
            (f'/group/{cls.group.slug}/', 'posts/group_list.html'),
            (f'/profile/{cls.user.username}/', 'posts/profile.html'),
            (cls.post_url, 'posts/post_detail.html'),
            (cls.post_create, 'posts/create.html'),
            (cls.post_edit, 'posts/create.html'),
        )
        cls.url_redirect = (
            (f'/posts/{cls.post.id}/edit/',
             f'/auth/login/?next=/posts/{cls.post.id}/edit/'),
            ('/create/',
             '/auth/login/?next=/create/'),
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(PostURLTests.user)
        cache.clear()

    def test_task_list_url_redirect_anonymous_on_admin_login(self):
        """Проверка редиректа анонимного пользователя"""
        for address, redirect in dict(PostURLTests.url_redirect).items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, (redirect))

    def test_url_exists_at_desired_location_guest(self):
        """Проверка статуса адреса для неавторизованного клиента"""
        for address, _ in dict(PostURLTests.public_urls[:4]).items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template_guest(self):
        """Проверка шаблонов по адресам для неавторизованного клиента"""
        for address, template in dict(PostURLTests.public_urls[:4]).items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_url_exists_at_desired_location_user(self):
        """Проверка статуса адреса для авторизованного клиента"""
        for address, _ in dict(PostURLTests.public_urls[:5]).items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template_user(self):
        """Проверка статуса адреса для авторизованного клиента"""
        for address, template in dict(PostURLTests.public_urls[:5]).items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_task_detail_url_exists_at_desired_location_authorized(self):
        """Проверка Not Found для несуществующей страницы"""
        response = self.authorized_client.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_url_exists_at_desired_location_author(self):
        """Проверка статуса адреса для автора постов"""
        for address, _ in dict(PostURLTests.public_urls).items():
            with self.subTest(address=address):
                response = self.authorized_author.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template_author(self):
        """Проверка использования правильного шаблона"""
        for address, template in dict(PostURLTests.public_urls).items():
            with self.subTest(address=address):
                response = self.authorized_author.get(address)
                self.assertTemplateUsed(response, template)
