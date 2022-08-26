import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
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

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_creat_post(self):
        """При создании через формы пост появляться с нужным текстом
        на странице пользователя"""
        post = Post.objects.count()
        form_data = {
            'text': 'Текст из формы',
            'image': self.uploaded,
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), post + 1)
        self.assertRedirects(
            response, reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ))
        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertEqual(Post.objects.filter(
            text=form_data['text'],
            image='posts/small.gif',
        ).exists(), True)

    def test_edit_post(self):
        """При редактировании поста он появляется с нужным текстом
        на странице поста и не создается новый пост"""
        post_edit = Post.objects.create(
            author=self.user,
            text='Пост котoрый нужно отредактировать',
            group=self.group,
        )
        data_edit = {
            "text": 'Пост после редактирования',
            "group": self.group.id,
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={"post_id": post_edit.id}),
            data=data_edit,
            follow=True,
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail',
                kwargs={'post_id': post_edit.id}
            ))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.filter(**data_edit).exists(), True)

    def test_form_commets(self):
        """Тест что после успешной отправки комментарий
        появляется на странице поста"""
        post_in_commit = Post.objects.create(
            author=self.user,
            text='Откомментируй меня полностью',
        )
        comment = {
            "post_id": post_in_commit.id,
            "author_id": self.user.id,
            'text': 'огонь'
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={"post_id": post_in_commit.id}),
            data=comment,
            follow=True,
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail',
                kwargs={'post_id': post_in_commit.id}
            ))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            Comment.objects.filter(**comment).exists(), True
        )
        comment_in_page = response.context.get('comments')[0]
        self.assertEqual(comment_in_page.text, comment['text'])
