import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='auth',
        )
        cls.user_2 = User.objects.create_user(
            username='author',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
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
        cls.post1 = Post.objects.create(
            author=cls.user,
            text='Тестовый постТестовыйпостпост',
            group=cls.group
        )
        cls.post2 = Post.objects.create(
            author=cls.user,
            text='Тестовый постТестовый постТестовый постТестовый пост',
            group=cls.group,
            image=cls.uploaded
        )
        cls.templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': cls.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:post_detail',
                kwargs={"post_id": cls.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:profile',
                kwargs={'username': cls.post.author}
            ): 'posts/profile.html',

        }
        cls.templates_pages_names_views = {
            reverse('posts:index'): 'posts/index.html',

            reverse(
                'posts:profile',
                kwargs={'username': cls.post.author}
            ): 'posts/profile.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': cls.group.slug}
            ): 'posts/group_list.html',
        }

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.user_2)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_404_castom(self):
        """"проверка на кастомный 404"""
        response = self.authorized_client.get('/net_takogo_adressa/')
        self.assertTemplateUsed(response, 'core/404.html')

    def test_pages_uses_correct_template(self):
        """ Проверка view-функциях используются правильные html-шаблоны."""
        for reverse_name, template in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                error = f'проверьте html-шаблоны в {template}'
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template, error)

    def test_post_pages_show_correct_context(self):
        """Шаблон post сформирован с правильным контекстом и
        передаются строки: фото, автора , текста, группы"""
        for name_page, template in self.templates_pages_names_views.items():
            with self.subTest(reverse_name=name_page):
                error = f'проверьте context в {template}'
                response = (self.authorized_client.
                            get(name_page))

                self.assertEqual(
                    response.context.get('post')
                    .author, self.post.author,
                    error,
                )
                self.assertEqual(
                    response.context.get('post')
                    .text, self.post.text,
                    error
                )
                self.assertEqual(
                    response.context.get('post')
                    .group, self.post.group,
                    error
                )
                self.assertEqual(
                    response.context.get('post')
                    .image, self.post.image,
                    error
                )

    def test_post_list_page_show_correct_context(self):
        """При создании объекта поста он попадает на нужные страницы,
        Так же  тут проверка сортировки,
        Проверка ФОТО подающие на странички."""
        for reverse_name, temp in self.templates_pages_names_views.items():
            message_error_output = f" Объекта нет в {temp} "
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                object_page = response.context['page_obj'][0]
                self.assertEqual(object_page.image, self.post2.image)
                post_id = object_page.pk
                self.assertEqual(post_id, self.post2.pk, message_error_output)

    def test_post_index_cache(self):
        """Проверка кеша на главной страницы"""
        post = Post.objects.create(
            author=self.user,
            text='удали меня',
        )
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertContains(response, post.text)
        Post.objects.filter(id=post.id).delete()
        response_cache = self.authorized_client.get(reverse('posts:index'))
        self.assertContains(response_cache, post.text)
        cache.clear()
        response_cache_del = self.authorized_client.get(reverse('posts:index'))
        self.assertNotContains(response_cache_del, post.text)

    def test_follow_create_and_del(self):
        """Авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок"""
        self.authorized_client.get(
            reverse(
                "posts:profile_follow",
                kwargs={"username": self.user_2}
            )
        )
        self.assertEqual(
            Follow.objects.filter(author=self.user_2).exists(),
            True
        )
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user_2}
        ))
        self.assertEqual(
            Follow.objects.filter(author=self.user_2).exists(),
            False
        )

    def test_follow_create_on_page_user(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех,
        кто не подписан."""
        post = Post.objects.create(
            text="попишись на меня",
            author=self.user_2
        )
        self.authorized_client.get(
            reverse(
                "posts:profile_follow",
                kwargs={"username": self.user_2}
            )
        )

        self.authorized_client.get(
            reverse(
                "posts:profile_follow",
                kwargs={"username": self.user_2}
            )
        )

        my_follows = self.authorized_client.get(
            reverse(
                "posts:follow_index",
            )
        )
        self.assertContains(my_follows, post.text)
        none_follows = self.author_client.get(
            reverse(
                "posts:follow_index",
            ))
        self.assertNotContains(none_follows, post.text)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='auth',
        )

        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post_list = [
            Post(
                text=f"Тест {i}",
                author=cls.user,
                group=cls.group,
            ) for i in range(15)
        ]
        cls.post = Post.objects.bulk_create(cls.post_list)

        cls.templates_pages_names_Paginator = {
            reverse('posts:index'): 'Главная',

            reverse(
                'posts:profile',
                kwargs={'username': cls.user}
            ): "Страница Пользователя",
            reverse(
                'posts:group_list',
                kwargs={'slug': cls.group.slug}
            ): "Страница Группы",
        }

    def setUp(self):
        cache.clear()

    def test_first_page_contains_ten_records(self):
        """При создании большого количество объектов поста,
        корректно отрабатывает Paginator."""
        for reverse_name, temp in self.templates_pages_names_Paginator.items():
            message_error_output = f"Проверь  Paginator на:{temp} "
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']),
                    settings.COUNT_POST_PAGE,
                    message_error_output
                )
