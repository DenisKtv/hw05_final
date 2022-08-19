from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.post = Post.objects.create(
            text='Тестовый текст ',
            author=cls.user,
            pub_date='тестовая дата',
        )
        cls.group = Group.objects.create(
            title='Тестовое имя',
            slug='test-group',
            description='Тестовое описание',
        )

    def test_object_name_is_text_field(self):
        post = PostModelTest.post
        expected_object = post.text
        self.assertEqual(expected_object, str(post))


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовое имя',
            slug='test-group',
            description='Тестовое описание',
        )

    def test_object_name_is_title_field(self):
        group = GroupModelTest.group
        expect_object = group.title
        self.assertEqual(expect_object, str(group))
