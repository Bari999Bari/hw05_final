from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post, Comment

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост 15 15',
        )
        cls.LIMIT_SYMBOLS = 15

    def test_post_model_have_correct_object_name(self):
        """Проверяем, что у модели Post корректно работает __str__."""
        post = PostModelTest.post
        expected_object_name_post = post.text[:self.LIMIT_SYMBOLS]
        self.assertEqual(expected_object_name_post, str(post))

    def test_post_model_have_correct_verbose_name(self):
        """Проверяем, что у полей модели Post корректные verbose_name."""
        template = {
            'text': 'Содержание',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Сообщество',
            'image': 'Картинка',
        }
        for field_name, content in template.items():
            with self.subTest(field_name=field_name):
                post_field_verbose_name = (
                    PostModelTest.post._meta.get_field(field_name).verbose_name
                )
                self.assertEqual(post_field_verbose_name, content)


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание',
            slug='test_slug',
        )

    def test_group_model_have_correct_object_name(self):
        """Проверяем, что у модели Group корректно работает __str__."""
        group = GroupModelTest.group
        expected_object_name_group = group.title
        self.assertEqual(expected_object_name_group, str(group))

    def test_group_model_have_correct_verbose_name(self):
        """Проверяем, что у полей модели Group корректные verbose_name."""
        template = {
            'title': 'Название',
            'description': 'Описание',
        }
        for field_name, content in template.items():
            with self.subTest(field_name=field_name):
                group_field_verbose_name = (
                    GroupModelTest.group._meta.get_field(
                        field_name).verbose_name)
                self.assertEqual(
                    group_field_verbose_name,
                    content)


class CommentModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост 15 15',
        )
        cls.comment = Comment.objects.create(
            text='sdf',
            author=cls.user,
            post=cls.post,
        )
        cls.LIMIT_SYMBOLS = 15

    def test_post_model_have_correct_verbose_name(self):
        """Проверяем, что у полей модели Comment корректные verbose_name."""
        template = {
            'text': 'Содержание',
            'created': 'Дата публикации',
            'author': 'Автор',
            'post': 'Запись',
        }
        for field_name, content in template.items():
            with self.subTest(field_name=field_name):
                post_field_verbose_name = (
                    CommentModelTest.comment.
                    _meta.get_field(field_name).verbose_name
                )
                self.assertEqual(post_field_verbose_name, content)
