import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from ..models import Post, Group, Comment, Follow
from ..forms import PostForm

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.user1 = User.objects.create_user(username='auth')
        cls.user2 = User.objects.create_user(username='name')
        cls.group1 = Group.objects.create(
            title='Тестовая группа',
            slug='slug1',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Текст названия группы',
            slug='slug2',
            description='Текстовое описание 2'
        )
        cls.form = PostForm()
        cls.post1 = Post.objects.create(
            author=PostPagesTests.user1,
            text='Текст поста',
            id=1,
            group=PostPagesTests.group1,
            image=PostPagesTests.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user2)
        self.post2 = Post.objects.create(
            author=PostPagesTests.user2,
            text='Пост',
            id=2,
            group=PostPagesTests.group2,
            image=PostPagesTests.uploaded,
        )
        cache.clear()

    def test_index_page_uses_correct_template(self):
        """URL-адрес правильно использует шаблон"""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': 'slug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': PostPagesTests.post1.author}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostPagesTests.post1.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostPagesTests.post1.id}
            ): 'posts/create.html',
            reverse(
                'posts:post_create'
            ): 'posts/create.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
        self.assertTemplateUsed(response, template)

    def test_create_page_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_create')
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField,
            'image': forms.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIn('page_obj', response.context)
        first_object = response.context['page_obj'][1]
        second_object = response.context['page_obj'][0]
        self.assertEqual(first_object.image, PostPagesTests.post1.image)
        self.assertEqual(first_object.text, PostPagesTests.post1.text)
        self.assertEqual(first_object.group, PostPagesTests.post1.group)
        self.assertEqual(first_object.id, PostPagesTests.post1.id)
        self.assertEqual(first_object.author, PostPagesTests.post1.author)
        self.assertEqual(second_object.image, self.post2.image)
        self.assertEqual(second_object.text, self.post2.text)
        self.assertEqual(second_object.group, self.post2.group)
        self.assertEqual(second_object.id, self.post2.id)
        self.assertEqual(second_object.author, self.post2.author)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': PostPagesTests.group1.slug})
        )
        self.assertEqual(
            response.context.get('group').title,
            PostPagesTests.group1.title)
        self.assertEqual(
            response.context.get('group').slug,
            PostPagesTests.group1.slug)
        self.assertEqual(
            response.context.get('group').description,
            PostPagesTests.group1.description)
        self.assertIn('page_obj', response.context)
        self.assertEqual(
            response.context['page_obj'][0].image,
            PostPagesTests.post1.image)
        self.assertEqual(
            response.context['page_obj'][0].text,
            PostPagesTests.post1.text)
        self.assertEqual(
            response.context['page_obj'][0].group,
            PostPagesTests.post1.group)
        self.assertEqual(
            response.context['page_obj'][0].id,
            PostPagesTests.post1.id)
        self.assertEqual(
            response.context['page_obj'][0].author,
            PostPagesTests.post1.author)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': PostPagesTests.post1.author})))
        self.assertIn('page_obj', response.context)
        self.assertEqual(
            response.context.get('author'),
            PostPagesTests.post1.author)
        self.assertEqual(
            response.context['page_obj'][0].image,
            PostPagesTests.post1.image)
        self.assertEqual(
            response.context['page_obj'][0].text,
            PostPagesTests.post1.text)
        self.assertEqual(
            response.context['page_obj'][0].group,
            PostPagesTests.post1.group)
        self.assertEqual(
            response.context['page_obj'][0].id,
            PostPagesTests.post1.id)
        self.assertEqual(
            response.context['page_obj'][0].author,
            PostPagesTests.post1.author)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': PostPagesTests.post1.id})))
        self.assertEqual(
            response.context.get('post').image,
            PostPagesTests.post1.image)
        self.assertEqual(
            response.context.get('post').text,
            PostPagesTests.post1.text)
        self.assertEqual(
            response.context.get('post').group,
            PostPagesTests.post1.group)
        self.assertEqual(
            response.context.get('post').id,
            PostPagesTests.post1.id)
        self.assertEqual(
            response.context.get('post').author,
            PostPagesTests.post1.author)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post2.id})))
        self.assertEqual(
            response.context.get('is_edit'), True)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField,
            'image': forms.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_new_post_show_page(self):
        """Шаблоны правильно отображают содержимое."""
        response = self.authorized_client.get(
            reverse('posts:index'))
        self.assertIn('page_obj', response.context)
        page_index = len(response.context['page_obj'])
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group2.slug}))
        page_group1 = len(response.context['page_obj'])
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user2.username}))
        page_profile1 = len(response.context['page_obj'])
        self.new_post = Post.objects.create(
            author=PostPagesTests.user2,
            text='Новый пост',
            id=3,
            group=PostPagesTests.group2,
            image=PostPagesTests.uploaded
        )
        cache.clear()
        response = self.authorized_client.get(
            reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), page_index + 1)
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group2.slug}))
        self.assertEqual(len(response.context['page_obj']), page_group1 + 1)
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user2}))
        self.assertEqual(len(response.context['page_obj']), page_profile1 + 1)
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group1.slug}))
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_show_post_detail_comment(self):
        self.new_comment = Comment.objects.create(
            author=PostPagesTests.user2,
            text='Новый коммент',
            post=PostPagesTests.post1,
        )
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': PostPagesTests.post1.id}))
        self.assertEqual(len(response.context['comments']), 1)


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='account')
        cls.group = Group.objects.create(
            title='Тест группа',
            slug='slug-cache',
            description='Описание',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(CacheTest.user)

    def test_cache_index_page(self):
        self.post = Post.objects.create(
            author=CacheTest.user,
            text='Текст',
            id=1,
            group=CacheTest.group,
        )
        response1 = self.authorized_client.get(
            reverse('posts:index'))
        self.post_del = Post.objects.get(id=1).delete()
        response2 = self.authorized_client.get(
            reverse('posts:index'))
        self.assertEqual(response1.content, response2.content)
        cache.clear()
        response3 = self.authorized_client.get(
            reverse('posts:index'))
        self.assertNotEqual(response3.content, response2.content)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='first')
        cls.user2 = User.objects.create_user(username='second')
        cls.user3 = User.objects.create_user(username='third')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slugger',
            description='Тестовое описание',
        )
        cls.post1 = Post.objects.create(
            author=FollowTest.user1,
            text='Текст поста',
            id=1,
            group=FollowTest.group,
        )

    def setUp(self):
        self.authorized_client1 = Client()
        self.authorized_client1.force_login(FollowTest.user2)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(FollowTest.user3)
        self.post2 = Post.objects.create(
            author=FollowTest.user1,
            text='Пост',
            id=2,
            group=FollowTest.group,
        )

    def test_follow_users(self):
        before_subscribe = Follow.objects.all()
        self.authorized_client1.get(
            reverse('posts:profile_follow',
                    kwargs={'username': FollowTest.user1.username})
        )
        self.assertTrue(Follow.objects.get(
            user=FollowTest.user2,
            author=FollowTest.user1
        ))
        self.authorized_client1.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': FollowTest.user1.username})
        )
        after_unsubscribe = Follow.objects.all()
        self.assertQuerysetEqual(before_subscribe, after_unsubscribe)

    def test_new_post_in_follow(self):
        self.authorized_client1.get(
            reverse('posts:profile_follow',
                    kwargs={'username': FollowTest.user1.username}
                    )
        )
        response_follow_index = self.authorized_client1.get(
            reverse('posts:follow_index')
        )
        response_unfollow_index = self.authorized_client2.get(
            reverse('posts:follow_index')
        )
        page_follow = len(response_follow_index.context['page_obj'])
        page_unfollow = len(response_unfollow_index.context['page_obj'])
        self.post3 = Post.objects.create(
            author=FollowTest.user1,
            text='Пост3',
            id=3,
            group=FollowTest.group,
        )
        response_follow_index = self.authorized_client1.get(
            reverse('posts:follow_index')
        )
        response_unfollow_index = self.authorized_client2.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(len(
            response_follow_index.context['page_obj']),
            page_follow + 1)
        self.assertEqual(len(
            response_unfollow_index.context['page_obj']),
            page_unfollow)
