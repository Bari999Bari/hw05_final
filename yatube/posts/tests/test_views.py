import shutil
import tempfile

from django.contrib.auth import get_user_model
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.conf import settings

from ..models import Post, Group

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PagesMultiPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание',
            slug='test_slug',
        )
        Post.objects.bulk_create([Post(
            author=cls.user,
            group=cls.group,
            text=f'{x}Тестовый пост 15 15',
        )
            for x in range(0, settings.POSTS_FOR_TESTING_QUANTITY)])
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_page_obj(self):
        """Проверка работы паджинатора для шаблонов URL."""
        templates_pages_names = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        for reverse_name in templates_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                obj_list = response.context.get('page_obj')
                response_2 = self.authorized_client.get(
                    reverse_name + '?page=2')
                obj_list_2 = response_2.context.get('page_obj')
                self.assertEqual(len(obj_list), settings.FIRST_PAGE_OBJ_COUNT)
                self.assertEqual(len(obj_list_2),
                                 settings.POSTS_FOR_TESTING_QUANTITY
                                 - settings.FIRST_PAGE_OBJ_COUNT)


class PagesSinglePageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание',
            slug='test_slug',
        )
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
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост 15 15',
            image=uploaded)
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user.username}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}):
                'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}):
                'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # def test_show_correct_context(self):
    #     """Проверка что шаблоны сформированы с верным контекстом."""
    #     templates_pages_names = (
    #         reverse('posts:index'),
    #         reverse('posts:group_list', kwargs={'slug': self.group.slug}),
    #         reverse('posts:profile',
    #         kwargs={'username': self.user.username}),
    #         reverse('posts:post_detail', kwargs={'post_id': self.post.pk}),
    #     )
    #     for reverse_name in templates_pages_names:
    #         with self.subTest(reverse_name=reverse_name):
    #             response = self.authorized_client.get(reverse_name)
    #             if reverse_name == reverse(
    #                     'posts:post_detail',
    #                     kwargs={'post_id': self.post.pk}):
    #                 first_object = response.context.get('post')
    #             else:
    #                 first_object = (
    #                     response.context.get('page_obj').object_list[0]
    #                 )
    #             self.assertEqual(first_object.text, self.post.text)
    #             self.assertEqual(first_object.author, self.user)
    #             self.assertEqual(first_object.group, self.group)
    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        first_object = (response.context.get('page_obj').object_list[0])
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.user)
        self.assertEqual(first_object.group, self.group)
        self.assertEqual(first_object.image, self.post.image)

    def test_index_use_cache(self):
        """Страница index использует кэш"""
        response = self.guest_client.get(reverse('posts:index'))
        Post.objects.create(
            author=self.user,
            text='victim',
            group=self.group)
        response_2 = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(response.content, response_2.content)

    def test_group_post_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}))
        first_object = (response.context.get('page_obj').object_list[0])
        second_object = (response.context.get('group'))
        self.assertEqual(second_object, self.group)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.user)
        self.assertEqual(first_object.group, self.group)
        self.assertEqual(first_object.image, self.post.image)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user.username}))
        first_object = (response.context.get('page_obj').object_list[0])
        second_object = (response.context.get('consumer'))
        self.assertEqual(second_object, self.user)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.user)
        self.assertEqual(first_object.group, self.group)
        self.assertEqual(first_object.image, self.post.image)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.pk}))
        first_object = response.context.get('post')
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.user)
        self.assertEqual(first_object.group, self.group)
        self.assertEqual(first_object.image, self.post.image)

    def test_create_post_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        templates_pages_names = (
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
        )
        for reverse_name in templates_pages_names:
            response = self.authorized_client.get(reverse_name)
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField,
            }

            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context['form'].fields[value]
                    self.assertIsInstance(
                        form_field, expected)

    def test_edit_post_page_show_correct_context_additional(self):
        """Проверка оставшихся полей в шаблоне редактирования поста."""
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.pk}))
        second_object = (response.context.get('is_edit'))
        third_object = (response.context.get('id'))
        self.assertTrue(second_object)
        self.assertEqual(third_object, self.post.pk)
