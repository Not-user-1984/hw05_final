from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostsURlTests(TestCase):
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
            text='Тестовый постТестовый пост',
            group=cls.group,
        )

        cls.url_names_and_templates = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.post.author}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{cls.post.id}/edit/': 'posts/create_post.html',
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }

    def setUp(self):
        cache.clear()

    def test_post_url_public_pages_authorized_and_guest_client(self):
        """Проверка доспупа всем клиентам """
        for address, message in self.url_names_and_templates.items():
            with self.subTest(message=message):
                error_name = f"Нет доступа:{message}"

                response = self.authorized_client.get(address, follow=True)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    error_name
                )

                response = self.client.get(address, follow=True)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    error_name
                )

    def test_post_url_edit_post_user_not_athor(self):
        """Проверка доспупа не автора поста к редактированию поста"""
        response = (
            self.client.get(f'/posts/{self.post.id}/edit/')
        )
        self.assertEqual(
            response.status_code,
            HTTPStatus.FOUND,
        )
        print(response)

    def test_post_url_commits_client(self):
        """Проверка доспупа к коментариям для гостя"""
        response = (self.client.get(f'posts/{self.post.id},/comment/'))
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND,)

    def test_post_url_commits_authorized_client(self):
        response = (
            self.authorized_client.get(
                f'posts/{self.post.id},/comment/,',
                follow=True)
        )
        self.assertEqual(
            response.status_code,
            HTTPStatus.NOT_FOUND,
        )

    def test_post_url_create_post_guest_client(self):
        """Проверка доспупа на переброс при создание поста гостем на
        страничку регистрации"""
        response = (
            self.client
            .get('/create/')
        )
        self.assertEqual(
            response.status_code,
            HTTPStatus.FOUND,
        )
        self.assertRedirects(
            response,
            ('/auth/login/?next=%2Fcreate%2F')
        )

    def test_urls_uses_correct_template(self):
        """Проверка что существуют шаблоны по правельным URL"""
        for address, template in self.url_names_and_templates.items():
            with self.subTest(address=address):
                error_name = f"Нет шаблона по адрессу:{address}"
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template, error_name)

    def test_error_page(self):
        response = self.client.get("/404/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
