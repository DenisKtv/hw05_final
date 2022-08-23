import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, Comment


User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestCreateForm(TestCase):
    """Тестируем на правильные HTML-шаблоны и context"""
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.authorized = Client()
        cls.authorized.force_login(cls.user)

        cls.group = Group.objects.create(
            title='Тестовое имя',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовая запись',
            author=cls.user,
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text='Тестовый текст',
            post=cls.post,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Проверка на создания новой записи и переадресации"""
        post_count = Post.objects.count()

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
            'group': TestCreateForm.group.id,
            'text': TestCreateForm.post.text,
            'image': uploaded,
        }
        response = self.authorized.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse(
                'posts:profile',
                kwargs={'username': TestCreateForm.post.author}
            )
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=TestCreateForm.group.id,
                text=TestCreateForm.post.text,
                image='posts/small.gif',
            ).exists()
        )

    def test_edit_post(self):
        """Проверка изменения поста"""
        form_data = {
            'group': TestCreateForm.group.id,
            'text': 'Новый текст'
        }
        response = self.authorized.post(
            reverse('posts:post_edit', kwargs={
                'post_id': f'{self.post.id}'}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{self.post.id}'}
            )
        )
        self.assertTrue(Post.objects.filter(
            id=self.post.id,
            group=TestCreateForm.group,
            text='Новый текст',
        ).exists()
        )

    def test_create_comment(self):
        """Тест на создание комментария"""
        form_data = {
            'author': TestCreateForm.user,
            'text': 'Тестовый текст',
            'post_id': TestCreateForm.post.id,
        }
        self.authorized.post(reverse('posts:add_comment', kwargs={
            'post_id': TestCreateForm.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertTrue(
            Comment.objects.filter(
                author=TestCreateForm.user,
                text='Тестовый текст',
                post_id=TestCreateForm.post.id,
            ).exists()
        )
