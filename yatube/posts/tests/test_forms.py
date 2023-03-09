from datetime import datetime
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from posts.models import Post, Group, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='user')
        cls.group = Group.objects.create(title='group',
                                         slug='test-slug')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            pub_date=datetime(2023, 2, 24, 14, 30, 0),
            author=cls.user
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый коммент'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        post_count = Post.objects.count()

        form_data = {'text': 'Тестовый текст2',
                     'pub_date': 'Тестовая дата2',
                     }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:profile',
                             kwargs={'username': self.user.username})
                             )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст2',
            ).exists()
        )

    def test_edit_post(self):
        """Валидная форма вносит изменения записи в Post."""
        post_count = Post.objects.count()

        form_data = {'text': 'Тестовый текст2',
                     'pub_date': 'Тестовая дата2',
                     }

        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={'post_id': self.post.id})
                             )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст2',
            ).exists()
        )

    def test_create_post_with_image_with_postform(self):
        """Проверяем, что при отправке поста с картинкой через форму PostForm
        создаётся запись в базе данных.
        """
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small4.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый пост с картинкой',
            'image': uploaded
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True)
        posts = Post.objects.filter(
            text='Тестовый пост с картинкой',
            image__isnull=False
        )
        self.assertTrue(posts.exists())

    def test_comment_from_authorized_user(self):
        """Проверяем, что комментировать посты может только авторизованный
        пользователь.
        """
        comment = Comment.objects.filter(
            text='Тестовый коммент'
        )
        self.assertTrue(comment.exists())

    def test_comment_from_guest_user(self):
        """Проверяем, что неавторизованный пользователь не может
        комментировать посты.
        """
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            {'text': 'Тестовый коммент от неавторизованного'})
        comment = Comment.objects.filter(
            text='Тестовый коммент от неавторизованного'
        )
        self.assertFalse(comment.exists())

    def test_comment_on_page_post_detail_after_post(self):
        """Проверяем, что после успешной отправки комментарий появляется
        на странице поста.
        """
        form_data = {'text': 'Тестовый комментарий'}
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertContains(response, 'Тестовый комментарий')
