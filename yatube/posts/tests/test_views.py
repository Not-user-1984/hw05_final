from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='auth',
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
            group=cls.group
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
            # reverse(
            #     '/404/',
            # ): 'core/404.html',
        }

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """ Проверка view-функциях используются правильные html-шаблоны."""
        for reverse_name, template in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                error = f'проверьте html-шаблоны в {template}'
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template, error)

    def test_post_pages_show_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""
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
                    'нет картинки'
                )

    def test_post_list_page_show_correct_context(self):
        """При создании объекта поста он попадает на нужные страницы."""
        for reverse_name, temp in self.templates_pages_names_views.items():
            message_error_output = f" Объекта нет в {temp} "
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                object_page = response.context['page_obj'][0]
                post_id = object_page.pk
                self.assertEqual(post_id, self.post2.pk, message_error_output)

    # def test_post_index_cache(self):
    #     post20sec = Post.objects.create(
    #         author=self.user,
    #         text='20 sec',
    #         group=self.group
    #     )
    #     response = self.client.get(reverse('posts:index'))
    #     htc = response.content
    #     Post.obects.get(pk=post20sec.pk)
    #     response = self.client.get(reverse('posts:index'))
    #     htcs = response.content
    #     p2 = response.content

        # self.assertTrue(count_obj_posts > 0)
        # posts = Post.objects.all()
        # caches = cache.get('index_page')
        #
        # response = self.client.get(reverse('posts:index'))


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
