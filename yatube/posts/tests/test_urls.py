from http import HTTPStatus
from datetime import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.core.cache import cache

from posts.models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='author')
        cls.not_author = User.objects.create(username='not_author')
        cls.group = Group.objects.create(title='Тестовая группа',
                                         slug='test-slug')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            pub_date=datetime(2023, 2, 24, 14, 30, 0),
            author=cls.user
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(self.not_author)

    def test_urls_uses_correct_template_for_authorized(self):
        """Проверка вызываемых HTML-шаблонов."""
        cache.clear()
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.get_username()}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_index_url_exists_at_desired_location(self):
        """Страница /index/ доступна любому пользователю."""
        response = self.guest_client.get('')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_group_url_exists_at_desired_location(self):
        """Страница /group/ доступна любому пользователю."""
        response = self.guest_client.get(f'/group/{self.group.slug}/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_profile_url_exists_at_desired_location(self):
        """Страница /profile/ доступна любому пользователю."""
        response = self.guest_client.get(f'/profile/{self.user.username}/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_url_exists_at_desired_location(self):
        """Страница /posts/ доступна любому пользователю."""
        response = self.guest_client.get(f'/posts/{self.post.id}/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexising_page_for_guest(self):
        """Проверяем, что несуществующая страница возвращает
        код 404 для неавторизованного пользователя.
        """
        response = self.guest_client.get('/unexisting/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_unexising_page_for_authorized(self):
        """Проверяем, что несуществующая страница возвращает
        код 404 для авторизованного пользователя.
        """
        response = self.authorized_client.get('/unexisting/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_create_page_for_guest_users(self):
        """Проверяем, что неавторизованного пользователя
        при попытке перейти на страницу создания поста
        перенаправляет на страницу авторизации.
        """
        response = self.guest_client.get('/create/')
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_edit_page_for_guest_users(self):
        """Проверяем, что неавторизованного пользователя
        при попытке перейти на страницу редактирования поста
        перенаправляет на страницу авторизации.
        """
        response = self.guest_client.get(f'/posts/{self.post.id}/edit/')
        self.assertRedirects(response,
                             f'/auth/login/?next=/posts/{self.post.id}/edit/'
                             )

    def test_edit_page_for_authorized_users_but_not_author(self):
        """Проверяем, что авторизованного пользователя, но не автора поста
        при попытке перейти на страницу редактирования поста
        перенаправляет на страницу самого поста.
        """
        response = self.authorized_client_not_author.get(f'/posts/'
                                                         f'{self.post.id}'
                                                         f'/edit/')
        self.assertRedirects(response,
                             f'/posts/{self.post.id}/'
                             )
