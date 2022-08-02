import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.cache import cache
from ..forms import PostForm, CommentForm
from ..models import Post, Group, Comment


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
class FormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='first',
            description='описание группы',
        )
        cls.post1 = Post.objects.create(
            group=FormTests.group,
            text='Текст до изменения',
            author=FormTests.user,
            id=1,
            image=None
        )
        cls.form = PostForm()
        cls.com_fotm = CommentForm()

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(FormTests.user)
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cache.clear()

    def test_valid_form_create(self):
        '''Проверка формы при создании'''
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста',
            'group': FormTests.group.pk,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        new_post_count = Post.objects.count()
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': FormTests.user.username}
        ))
        self.assertNotEqual(posts_count, new_post_count)
        self.assertTrue(
            Post.objects.filter(
                text='Текст поста',
                group=FormTests.group,
                image='posts/small.gif',
            ).exists()
        )

    def test_valid_form_edit(self):
        '''Проверка формы при редактировании'''
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст пост',
            'group': FormTests.group.pk,
            'image': self.uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': FormTests.post1.id}),
            data=form_data,
            follow=True)
        edit_post_count = Post.objects.count()
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': FormTests.post1.id}
        ))
        self.assertEqual(posts_count, edit_post_count)
        self.assertTrue(
            Post.objects.filter(
                text='Текст пост',
                group=FormTests.group,
                image='posts/small.gif',
            ).exists())

    def test_comment_only_authorized_client(self):
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Первый комментарий'
        }
        self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': FormTests.post1.id}),
            data=form_data,
            follow=True,
        )
        new_comment_count = Comment.objects.count()
        self.assertNotEqual(comments_count, new_comment_count)
        self.assertTrue(
            Comment.objects.filter(
                text='Первый комментарий'
            ).exists())

    def test_comment_only_guest_client(self):
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Второй комментарий'
        }
        self.guest_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': FormTests.post1.id}),
            data=form_data,
            follow=True,
        )
        new_comment_count = Comment.objects.count()
        self.assertEqual(comments_count, new_comment_count)
