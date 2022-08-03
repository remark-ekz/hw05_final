from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from ..models import Post, Group

User = get_user_model()


class PaginatorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.bulk_create(
            [Post(
                author=PaginatorTest.user,
                text=f'Текст поста №{number}',
                group=PaginatorTest.group,
                id=number,
            )
                for number in range(13)
            ]
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorTest.user)
        cache.clear()

    def test_index_first_page_paginator(self):
        """Проверка пагинации первой страницы index"""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_index_second_page_paginator(self):
        """Проверка пагинации второй страницы index"""
        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_group_list_first_page_paginator(self):
        """Проверка пагинации первой страницы group_list"""
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': PaginatorTest.group.slug})
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_group_list_second_page_paginator(self):
        """Проверка пагинации второй страницы group_list"""
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': PaginatorTest.group.slug}) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_profile_first_page_paginator(self):
        """Проверка пагинации первой страницы profile"""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': PaginatorTest.user.username})
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_profile_second_page_paginator(self):
        """Проверка пагинации второй страницы profile"""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': PaginatorTest.user.username}) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 3)
