from datetime import datetime

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from django.core.cache import cache

from posts.models import Post, Group, Follow
from posts.forms import PostForm

User = get_user_model()


class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()
        cls.user = User.objects.create(username='user')
        cls.other_user = User.objects.create(username='other_user')
        cls.group = Group.objects.create(title='Тестовая группа',
                                         slug='test-slug')
        cls.other_group = Group.objects.create(title='Другая группа',
                                               slug='test-slug2')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            pub_date=datetime(2023, 2, 24, 15, 30, 0),
            author=cls.user,
            group=cls.group
        )
        cls.other_post = Post.objects.create(
            text='Другой текст',
            pub_date=datetime(2023, 2, 24, 15, 30, 0),
            author=cls.other_user,
            group=cls.other_group
        )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': 'test-slug'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.user.username}):
            'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}):
            'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
            'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_show_correct_context(self):
        urls = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        )

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                post = response.context.get('post')
                self.assertEqual(post, self.post)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_detail',
                                              kwargs={'post_id': self.post.id})
                                              )
        first_object = response.context['post']
        post_text_0 = first_object.text
        post_pub_date_0 = first_object.pub_date
        post_author_0 = first_object.author
        post_group_0 = first_object.group.title
        first_objects = {
            post_text_0: self.post.text,
            post_pub_date_0: self.post.pub_date,
            post_author_0: self.post.author,
            post_group_0: self.group.title
        }
        for post_text, expected in first_objects.items():
            with self.subTest(value=post_text):
                self.assertEqual(post_text, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_edit',
                                              kwargs={'post_id': self.post.id})
                                              )
        form = PostForm()
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        context = response.context
        self.assertTrue('is_edit' in context)
        self.assertEqual(context['is_edit'], True)
        self.assertIsInstance(context['is_edit'], bool)
        self.assertIsInstance(form, PostForm)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form = response.context.get('form')
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertIsNotNone(form)
        self.assertIsInstance(form, PostForm)

    def test_post_create_on_index_page(self):
        """Проверяем, что если при создании поста указать группу, то этот пост
        появляется на главной странице сайта.
        """
        user = self.user
        self.client.force_login(user)
        post = self.post
        response = self.client.get(reverse('posts:index'))
        self.assertContains(response, post)

    def test_post_create_on_group_list_page(self):
        """Проверяем, что если при создании поста указать группу, то этот пост
        появляется на странице выбранной группы.
        """
        user = self.user
        group = self.group
        self.client.force_login(user)
        post = self.post
        response = self.client.get(reverse('posts:group_list',
                                   kwargs={'slug': group.slug})
                                   )
        self.assertContains(response, post.text)

    def test_post_create_on_profile_page(self):
        """Проверяем, что если при создании поста указать группу, то этот пост
        появляется в профайле пользователя.
        """
        user = self.user
        self.client.force_login(user)
        post = self.post
        response = self.client.get(reverse('posts:profile',
                                   kwargs={'username': user})
                                   )
        self.assertContains(response, post.text)

    def test_post_create_on_right_group(self):
        """Проверяем, что пост попадает в группу, для которой предназначен."""
        group = self.group
        post = self.post
        response = self.client.get(reverse('posts:group_list',
                                   kwargs={'slug': group.slug})
                                   )
        self.assertContains(response, post.text)

    def test_post_create_on_wrong_group(self):
        """Проверяем, что пост не попадает в группу, для которой не
        предназначен.
        """
        group = self.other_group
        post = self.post
        response = self.client.get(reverse('posts:group_list',
                                   kwargs={'slug': group.slug})
                                   )
        self.assertNotContains(response, post.text)

    def test_auth_user_subscribe_and_unsubscribe_on_authors(self):
        """Проверяем, что авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок.
        """
        response = self.authorized_client.post(
            reverse('posts:profile_follow', kwargs={'username':
                                                    self.other_user.username}),
            follow=True
        )
        following = Follow.objects.filter(user=self.user,
                                          author=self.other_user.id).exists()
        response = self.authorized_client.post(
            reverse('posts:profile_follow', kwargs={'username':
                                                    self.other_user.username}),
            follow=True
        )
        follower_count = Follow.objects.filter(author=self.other_user).count()
        self.assertTrue(following)
        self.assertEqual(follower_count, 1)
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username':
                                             self.other_user.username})
        )
        response = self.authorized_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.other_user.username}
            ),
            follow=True
        )
        following = not Follow.objects.filter(
            user=self.user,
            author=self.other_user.id
        ).exists()
        self.assertTrue(following)

    def test_new_post_view_on_follow_page_who_subscribe(self):
        """Проверяем, что новая запись пользователя появляется в ленте тех,
        кто на него подписан.
        """
        self.authorized_client.post(
            reverse('posts:profile_follow', kwargs={'username':
                                                    self.other_user.username}),
            follow=True
        )
        new_post = self.other_post
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertContains(response, new_post)

    def test_new_post_not_view_on_follow_page_who_not_subscribe(self):
        """Проверяем, что новая запись пользователя не появляется в ленте тех,
        кто на него не подписан.
        """
        new_post = self.other_post
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotContains(response, new_post)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='user2')
        cls.group = Group.objects.create(title='Тестовая группа2',
                                         slug='test-slug2')
        Post.objects.bulk_create([
            Post(text=f'Тестовый пост {i}',
                 author=cls.user,
                 group=cls.group) for i in range(1, 14)
        ])

    def setUp(self):
        cache.clear()

    def test_first_page_contains_ten_records_for_index(self):
        """Проверяем, что количество постов на первой странице шаблона index
        равно 10.
        """
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records_for_index(self):
        """Проверяем, что количество постов на второй странице шаблона index
        равно 3.
        """
        response = self.client.get(reverse('posts:index'), {'page': 2})
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_page_contains_ten_records_for_group_list(self):
        """Проверяем, что количество постов на второй странице шаблона
        group_list равно 10.
        """
        response = self.client.get(reverse('posts:group_list',
                                   kwargs={'slug': self.group.slug})
                                   )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records_for_group_list(self):
        """Проверяем, что количество постов на второй странице шаблона
        group_list равно 3.
        """
        response = self.client.get(reverse('posts:group_list',
                                   kwargs={'slug':
                                           self.group.slug}), {'page': 2}
                                   )
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_page_contains_ten_records_for_profile(self):
        """Проверяем, что количество постов на второй странице шаблона
        profile равно 10.
        """
        cache.clear()
        response = self.client.get(reverse('posts:profile',
                                   kwargs={'username': self.user.username})
                                   )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records_for_profile(self):
        """Проверяем, что количество постов на второй странице шаблона
        profile равно 3.
        """
        cache.clear()
        response = self.client.get(reverse('posts:profile',
                                   kwargs={'username':
                                           self.user.username}), {'page': 2}
                                   )
        self.assertEqual(len(response.context['page_obj']), 3)


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='username')

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache(self):
        """Проверяем работу кэша."""
        cache.clear()
        Post.objects.bulk_create([
            Post(text=f'Тестовый пост {i}',
                 author=self.user) for i in range(1, 4)
        ])
        posts = (
            'Тестовый пост 1',
            'Тестовый пост 2',
            'Тестовый пост 3'
        )
        response = self.authorized_client.get(reverse('posts:index'))
        for post in posts:
            with self.subTest(post=post):
                self.assertContains(response, post)

        Post.objects.all().delete()

        response = self.authorized_client.get(reverse('posts:index'))
        self.assertContains(response, 'Тестовый пост 1')

        cache.clear()

        response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotContains(response, 'Тестовый пост 1')
