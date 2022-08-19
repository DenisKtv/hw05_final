from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.core.cache import cache

from posts.models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    def test_homepage(self):
        guest_client = Client()
        response = guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)


class PostsUrlTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        cls.guest = Client()

        cls.user = User.objects.create_user(username='user')
        cls.authorized = Client()
        cls.authorized.force_login(cls.user)

        cls.author = User.objects.create_user(username='author')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.group = Group.objects.create(
            title='Тестовое имя',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст',
            group=cls.group,
        )
        cls.address_profile = '/profile/author/'
        cls.address_group = '/group/test-slug/'
        cls.address_create = '/create/'
        cls.address_post_edit = f'/posts/{cls.post.id}/edit/'
        cls.address_post_id = f'/posts/{cls.post.id}/'
        cls.address_comment = f'/posts/{cls.post.id}/comment/'

    def setUp(self) -> None:
        cache.clear()

    def test_post_and_group_for_guest(self):
        """Тест доступности страниц для клиентов"""
        url = [
            ('/', self.guest, HTTPStatus.OK),
            (self.address_group, self.guest, HTTPStatus.OK),
            (self.address_profile, self.guest, HTTPStatus.OK),
            (self.address_post_id, self.guest, HTTPStatus.OK),
            ('/unexisting_page/', self.guest, HTTPStatus.NOT_FOUND),
            (self.address_create, self.guest, HTTPStatus.FOUND),
            (self.address_post_edit, self.guest, HTTPStatus.FOUND),
            (self.address_create, self.authorized, HTTPStatus.OK),
            (self.address_post_edit, self.author_client, HTTPStatus.OK),
            (self.address_comment, self.guest, HTTPStatus.FOUND),
        ]
        for address in url:
            with self.subTest():
                response = address[1].get(address[0])
                self.assertEqual(response.status_code, address[2])

    def test_redirect_anonymous_from_create_and_edit_on_login(self):
        """Тест переадресации клиента-гостя"""
        response = self.guest.get(self.address_create, follow=True)
        response_2 = self.guest.get(self.address_post_edit, follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertRedirects(response_2, '/auth/login/?next=/posts/1/edit/')

    def test_urls_templates(self):
        templates_url_names = {
            '/': 'posts/index.html',
            self.address_group: 'posts/group_list.html',
            self.address_profile: 'posts/profile.html',
            self.address_post_id: 'posts/post_detail.html',
            self.address_post_edit: 'posts/post_create.html',
            self.address_create: 'posts/post_create.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized.get(address)
                self.assertTemplateUsed(response, template)

    def test_cooment_page_for_authorized_only(self):
        """Страница /comment/ доступна только авторизованному пользователю."""
        response = self.authorized.get(self.address_comment, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
