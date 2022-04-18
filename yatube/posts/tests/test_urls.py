from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    def test_homepage(self):
        # Создаем экземпляр клиента
        guest_client = Client()
        # Делаем запрос к главной странице и проверяем статус
        response = guest_client.get('/')
        # Утверждаем, что для прохождения теста код должен быть равен 200
        self.assertEqual(response.status_code, HTTPStatus.OK)


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_not_author = User.objects.create_user(username='auth2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание',
            slug='test_slug',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост 15 15',
        )
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client_not_author = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_client_not_author.force_login(cls.user_not_author)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk}): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:follow_index'): 'posts/follow.html',
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user.username}): 'posts/index.html',
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user.username}): 'posts/index.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_exist(self):
        """URL-адреса существуют"""
        urls_statuses = {
            reverse('posts:index'): HTTPStatus.OK,
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): HTTPStatus.OK,
            reverse('posts:profile',
                    kwargs={'username': self.user.username}): HTTPStatus.OK,
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.pk}): HTTPStatus.OK,
            'nonexist': HTTPStatus.NOT_FOUND,
        }
        urls_statuses_for_authorized_client = {
            reverse('posts:post_create'): HTTPStatus.OK,
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.pk}): HTTPStatus.OK,
        }
        for address, status in urls_statuses.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status)
        for address, status in urls_statuses_for_authorized_client.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, status)

    def test_post_edit_url_not_allowed_to_notAuthor(self):
        """Страница /posts/1/edit/ недоступна не автору поста."""
        response = self.authorized_client_not_author.get(
            f'/posts/{self.post.pk}/edit/',
            follow=False,
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_create_post_not_allowed_to_unauthorized(self):
        """Страница /create/ недоступна неавторизованым пользователям."""
        response = self.guest_client.get('/create/', follow=False)
        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
