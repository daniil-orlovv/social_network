from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='user')
        cls.post = Post.objects.create(
            text='Тестовый текст более 15 символов',
            author=cls.user
        )
        cls.group = Group.objects.create(
            title='Тестовое название'
        )

    def test_post_models_have_correct_object_name(self):
        """Проверяем, что для класса Post — выводятся первые пятнадцать
        символов поста.
        """
        post_value = str(self.post)
        expected_value = self.post.text[:15]
        self.assertEqual(post_value, expected_value)

    def test_group_models_have_correct_object_name(self):
        """Проверяем, что для класса Group — выводится название группы."""
        group_value = str(self.group)
        expected_value = self.group.title
        self.assertEqual(group_value, expected_value)
