import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, Group, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


# ¯\_(ツ)_/¯
# @override_settings(ROOT_URLCONF='/media/')
class PostCreateEditFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_not_author = User.objects.create_user(
            username='auth_not_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание',
            slug='test_slug',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа2',
            description='Тестовое описание2',
            slug='test_slug2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост 15 15', )
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client_not_author = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_client_not_author.force_login(cls.user_not_author)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post_authorized_full(self):
        """
        Валидная форма создает запись в Post
        если пользователь авторизован.
        """
        tasks_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст из формы',
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), tasks_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст из формы',
                group=self.group.pk,
                author=self.user.pk,
                # image='posts/small.gif'
            ).exists()
        )

    def test_create_post_authorized_without_group(self):
        """
        Валидная форма создает запись в Post
        если пользователь авторизован,
        но неуказана группа.
        """
        tasks_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст из формы',
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), tasks_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст из формы',
                group=None,
                author=self.user.pk,
            ).exists()
        )

    def test_create_post_unauthorized(self):
        """
        Валидная форма не создает запись в Post
        если пользователь не авторизован.
        """
        tasks_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст из формы',
            'group': self.group.pk,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertEqual(Post.objects.count(), tasks_count)

    def test_post_edit_unauthorized(self):
        """
        При POST запросе неавторизованного
        пользователя пост не будет отредактирован.
        """
        form_data = {
            'text': 'Тестовый текст из формы Редактированный',
            'group': self.group.pk,
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True,
        )
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый пост 15 15',
                # не понял как это из формы
                group=self.group.pk,
                author=self.user.pk,
                pub_date=self.post.pub_date,
            ).exists()
        )
        self.assertRedirects(response,
                             f'/auth/login/?next=/posts/{self.post.pk}/edit/')

    def test_post_edit_authorized_not_author(self):
        """
        При POST запросе авторизованного пользователя,
        но не автора поста, post не будет отредактирован
        """
        form_data = {
            'text': 'Тестовый текст из формы Редактированный',
            'group': self.group.pk,
        }
        response = self.authorized_client_not_author.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
        )
        self.assertTrue(
            Post.objects.filter(
                text=self.post.text,
                group=self.group.pk,
                author=self.user.pk,
                pub_date=self.post.pub_date,
            ).exists()
        )
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.post.pk}))

    def test_post_edit_authorized_author_without_change_group(self):
        """
        При POST запросе авторизованного пользователя,
        автора поста, post будет отредактирован без изменения группыю
        """
        form_data = {
            'text': 'Тестовый текст из формы Редактированный',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse(
                                 'posts:post_detail',
                                 kwargs={'post_id': self.post.pk})
                             )
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст из формы Редактированный',
                group=self.group.pk,
                author=self.user.pk,
                pub_date=self.post.pub_date,
            ).exists()
        )

    def test_post_edit_authorized(self):
        """
        При POST запросе авторизованного пользователя,
        автора поста, post будет отредактирован.
        """
        form_data = {
            'text': 'Тестовый текст из формы Редактированный',
            'group': self.group2.pk
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse(
                                 'posts:post_detail',
                                 kwargs={'post_id': self.post.pk})
                             )
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст из формы Редактированный',
                group=self.group2.pk,
                author=self.user.pk,
                pub_date=self.post.pub_date,
            ).exists()
        )

    def test_add_comment_authorized(self):
        """
        При POST запросе авторизованного пользователя,
        comment будет создан.
        """
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый коммент',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertRedirects(response,
                             reverse(
                                 'posts:post_detail',
                                 kwargs={'post_id': self.post.pk})
                             )
        self.assertTrue(
            Comment.objects.filter(
                text='Тестовый коммент',
                post=self.post,
                author=self.user.pk,
            ).exists()
        )

    def test_add_comment_unauthorized(self):
        """
        При POST запросе неавторизованного пользователя,
        comment не будет создан.
        """
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый коммент',
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
        )
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
