from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='auth')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый постТестовый постТестовый постТестовый пост',
            group=cls.group
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у модели Post корректно работает __str__."""
        error_name = f"вывод не имеет{settings.NUM_VERBS_STR} длину символов"
        self.assertEquals(
            self.post.__str__(),
            self.post.text[:settings.NUM_VERBS_STR],
            error_name
        )

    def test_models_group_have_str_title(self):
        """Проверяем, что у модели Group корректно работает __str__."""
        error_name = "вывод не имеет метода __str__ title"
        self.assertEquals(
            self.group.__str__(),
            self.group.title,
            error_name
        )
