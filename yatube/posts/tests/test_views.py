from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.conf import settings
from django.core.cache import cache

from posts.models import Group, Post

User = get_user_model()


class PostViewsTest(TestCase):
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
        cls.group_2 = Group.objects.create(
            title='Тестовое имя2',
            slug='test-slug2',
            description='Тестовое описание2',
        )
        cls.post = Post.objects.create(
            text='Тестовая запись',
            author=cls.user,
            group=cls.group,
            # image='Тестовая картинка',
        )

    def setUp(self) -> None:
        cache.clear()

    def test_pages_uses_correct_template(self):
        """Проверка на правильные HTML-шаблоны"""
        template_names = {
            reverse('posts:main_page'): 'posts/index.html',
            reverse('posts:group_posts_list', kwargs={'slug': 'test-slug'}): (
                'posts/group_list.html'
            ),
            reverse('posts:profile', kwargs={'username': f'{self.user}'}): (
                'posts/profile.html'
            ),
            reverse('posts:post_detail', kwargs={
                'post_id': f'{self.post.id}'}): ('posts/post_detail.html'),
            reverse('posts:post_edit', kwargs={
                'post_id': f'{self.post.id}'}): 'posts/post_create.html',
            reverse('posts:post_create'): 'posts/post_create.html',
        }
        for reverse_name, template in template_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_custom_404_page(self):
        """Проверка кастомной страницы ошибки 404"""
        response = self.authorized.get('/unexisting_page/')
        self.assertTemplateUsed(response, 'core/404.html')

    def test_home_page_show_correct_context(self):
        """Проверка контекста главной страницы"""
        response = self.authorized.get(reverse('posts:main_page'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        post_image = first_object.image
        self.assertEqual(post_image, PostViewsTest.post.image)
        self.assertEqual(post_text_0, PostViewsTest.post.text)
        self.assertEqual(post_author_0, PostViewsTest.post.author)
        self.assertEqual(post_group_0, PostViewsTest.post.group)

    def test_group_page_show_correct_context(self):
        """Проверка контекста в group_list"""
        response = self.authorized.get(
            reverse('posts:group_posts_list',
                    kwargs={'slug': PostViewsTest.group.slug}))
        post_title = response.context['group'].title
        post_slug = response.context['group'].slug
        post_description = response.context['group'].description
        post_image = Post.objects.first().image
        self.assertEqual(post_image, PostViewsTest.post.image)
        self.assertEqual(post_title, PostViewsTest.group.title)
        self.assertEqual(post_slug, PostViewsTest.group.slug)
        self.assertEqual(post_description, PostViewsTest.group.description)

    def test_profile_show_correct_context(self):
        """Проверка контекста в profile"""
        response = self.authorized.get(
            reverse('posts:profile',
                    kwargs={'username': PostViewsTest.post.author}))
        first_object = response.context['page_obj'][0]
        post_text = first_object.text
        post_author = first_object.author
        post_image = first_object.image
        self.assertEqual(post_image, PostViewsTest.post.image)
        self.assertEqual(post_author, PostViewsTest.post.author)
        self.assertEqual(post_text, PostViewsTest.post.text)

    def test_post_detail_show_correct_context(self):
        """Проверка контекста в post_detail"""
        response = self.authorized.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': PostViewsTest.post.id}))
        post_text = response.context['post'].text
        post_id = response.context['post'].id
        post_image = response.context['post'].image
        self.assertEqual(post_image, PostViewsTest.post.image)
        self.assertEqual(post_id, PostViewsTest.post.id)
        self.assertEqual(post_text, PostViewsTest.post.text)

    def test_create_post_edit_show_correct_context(self):
        """Проверка контекста в create_post_edit"""
        response = self.authorized.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostViewsTest.post.id}))
        post_text = response.context['post'].text
        post_id = response.context['post'].id
        self.assertEqual(post_id, PostViewsTest.post.id)
        self.assertEqual(post_text, PostViewsTest.post.text)

    def test_create_post_show_correct_context(self):
        """Тест контекстa в create_post"""
        response = self.authorized.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_new_post_in_main_group_profile_pages(self):
        """Тест, что пост при создании с группой появляется на страницах"""
        address_list = (
            reverse('posts:main_page'),
            reverse('posts:group_posts_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': f'{self.user}'}),
        )
        for address in address_list:
            with self.subTest(address=address):
                response = self.authorized.get(address)
                first_object = response.context['page_obj'][0]
                post_text = first_object.text
                post_author = first_object.author
                post_group = first_object.group
                self.assertEqual(post_text, PostViewsTest.post.text)
                self.assertEqual(post_author, PostViewsTest.post.author)
                self.assertEqual(post_group, PostViewsTest.post.group)

    def test_cache_in_main_page(self):
        response = self.authorized.get(reverse('posts:main_page'))
        first_obj = response.content
        Post.objects.all().delete()
        response_after_delete = self.authorized.get(reverse('posts:main_page'))
        second_obj = response_after_delete.content
        cache.clear()
        response_cache_clear = self.authorized.get(reverse('posts:main_page'))
        third_obj = response_cache_clear.content
        self.assertEqual(first_obj, second_obj)
        self.assertNotEqual(first_obj, third_obj)

    def test_in_post_another_group(self):
        """Тест что пост не попал в другую группу"""
        response = self.authorized.get(
            reverse('posts:group_posts_list',
                    kwargs={'slug': PostViewsTest.group_2.slug}))
        count_post = len(response.context['page_obj'])
        self.assertEqual(count_post, 0)


class TestPaginator(TestCase):
    """Тестируем пагинатор"""
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
        POSTS_FOR_TEST = settings.POSTS_PER_PAGE + 3
        objs = [
            Post(
                text='Тестовая запись',
                author=cls.user,
                group=cls.group,
            )
            for i in range(POSTS_FOR_TEST)
        ]
        Post.objects.bulk_create(objs)

    def test_paginator_pages(self):
        """Тест пагинатора первых страниц профиля, групп и главной"""
        address_names = [
            reverse('posts:main_page'),
            reverse('posts:group_posts_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': f'{self.user}'}),
        ]
        for reverse_name in address_names:
            with self.subTest():
                response = self.authorized.get(reverse_name)
                self.assertEqual(len(
                    response.context['page_obj']), settings.POSTS_PER_PAGE)
                response_2 = self.authorized.get(reverse_name + '?page=2')
                self.assertEqual(len(
                    response_2.context['page_obj']), 3)
