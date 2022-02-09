import shutil
import tempfile
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from ..models import Comment, Follow, Group, Post, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='TestAuthor')
        cls.authorized = User.objects.create_user(username='TestUser')
        cls.not_follower = User.objects.create_user(username='NotFollower')
        cls.test_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='test.gif',
            content=cls.test_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Test title',
            slug=cls.author,
            description='Test description',
        )
        cls.post = Post.objects.create(
            text='Test text',
            author=cls.author,
            group=cls.group,
            image=cls.uploaded,
        )
        cls.templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': cls.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': cls.post.author}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': cls.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': cls.post.id}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.authorized_client = Client()
        self.not_follower_client = Client()
        self.author_client.force_login(PostPagesTests.author)
        self.authorized_client.force_login(PostPagesTests.authorized)
        self.not_follower_client.force_login(PostPagesTests.not_follower)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, template in PostPagesTests.templates_page_names.items():
            with self.subTest(template=template):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_edit_create_pages_show_correct_context(self):
        """Шаблоны create, edit сформированы с правильным контекстом."""
        pages_names = {
            (reverse('posts:post_edit', kwargs={'post_id': self.post.id})
             ): 'form',
            reverse('posts:post_create'): 'form',
        }
        for address, form in pages_names.items():
            response = self.author_client.get(address)
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.models.ModelChoiceField,
            }
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get(form).fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_posts_pages_show_correct_context(self):
        """Шаблоны index, group_list, profile, сформированы
        с правильным контекстом.
        """
        pages_names = {
            reverse('posts:index'): 'page_obj',
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): 'page_obj',
            reverse(
                'posts:profile', kwargs={'username': self.author}
            ): 'page_obj',
        }
        for address, form in pages_names.items():
            response = self.author_client.get(address)
            form_obj_0 = response.context.get(form)[0]
            obj_fields = {
                form_obj_0.author: self.post.author,
                form_obj_0.id: self.post.id,
                form_obj_0.text: self.post.text,
                form_obj_0.pub_date: self.post.pub_date,
                form_obj_0.group.slug: str(self.group.slug),
                form_obj_0.image: self.post.image,
            }
            for form_value, expected in obj_fields.items():
                with self.subTest(form_value=form_value):
                    self.assertEqual(form_value, expected)

    def test_index_page_list_is_1(self):
        """На страницу со списком постов передаётся
        ожидаемое количество объектов
        """
        response = self.author_client.get(reverse('posts:index'))
        self.assertEqual(response.context['page_obj'].paginator.count, 1)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом.
        """
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        fields = {
            response.context['post'].id: self.post.id,
            response.context['post'].text: self.post.text,
            response.context['post'].author: self.post.author,
            response.context['post'].group: self.group,
            response.context['post'].pub_date: self.post.pub_date,
            response.context['post'].image: self.post.image,
        }
        for field, expected in fields.items():
            with self.subTest(field=field):
                self.assertEqual(field, expected)

    def test_post_with_group_is_on_pages(self):
        """Пост с группой появляется на страницах
        index, group_list, profile."""
        group_2 = Group.objects.create(
            title='Test title another group',
            slug='AnotherGroup',
            description='Test description another group',
        )
        pages_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.post.author}),
        ]
        for address in pages_names:
            response = self.authorized_client.get(address)
            form_obj_0 = response.context.get('page_obj')[0]
            self.assertEqual(form_obj_0.group.slug, str(self.group.slug))
            self.assertNotEqual(form_obj_0.group.slug, group_2.slug)

    def test_index_cache(self):
        """Проверка работы кэша"""
        post = Post.objects.create(
            author=PostPagesTests.author,
            text='Test cache'
        )
        response = self.guest_client.get(reverse('posts:index'))
        content = response.content
        post.delete()
        response_2 = self.guest_client.get(reverse('posts:index'))
        content_2 = response_2.content
        self.assertEqual(content, content_2)
        cache.clear()
        response_3 = self.guest_client.get(reverse('posts:index'))
        content_3 = response_3.content
        self.assertNotEqual(content, content_3)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.BATCH_SIZE = 13
        cls.author = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Test title',
            slug=cls.author,
            description='Test description',
        )
        cls.posts_list = [
            Post(
                author=cls.author,
                text=f'Текст {i}',
                group=cls.group
            )
            for i in range(cls.BATCH_SIZE)
        ]
        Post.objects.bulk_create(cls.posts_list)

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.author)
        cache.clear()

    def test_pages_contains_correct_number_records(self):
        """Количество постов на 1-2 странице == 10|3."""
        pages_names = {
            reverse('posts:index'): ['', '?page=2'],
            (reverse('posts:group_list', kwargs={'slug': self.group.slug})
             ): ['', '?page=2'],
            (reverse('posts:profile', kwargs={'username': self.author})
             ): ['', '?page=2'],
        }
        for address, page_list in pages_names.items():
            for i, page in enumerate(page_list):
                with self.subTest(address=address):
                    response = self.guest_client.get(address + page)
                    num = 10 if i == 0 else 3
                    self.assertEqual(
                        response.context['page_obj']
                        .paginator.page(i + 1)
                        .object_list.count(), num)


class CommentPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ADDED_ENTRY = 1
        cls.author = User.objects.create_user(username='TestAuthor')
        cls.post = Post.objects.create(
            text='Test text',
            author=cls.author,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.author,
            text='Test comment',
        )

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(CommentPagesTests.author)
        self.comments_count = Comment.objects.count()

    def test_comment_appears_in_post(self):
        """комментарий появляется на странице поста."""
        pages_names = [
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
        ]
        for address in pages_names:
            response = self.author_client.get(address)
            form_obj = response.context.get('comments')[0]
            self.assertEqual(form_obj.text, CommentPagesTests.comment.text)

    def test_post_can_comments_authorized_client(self):
        """Авторизованный пользователь может комментировать посты."""
        form_data = {
            'text': 'Test comment',
            'author': CommentPagesTests.author,
            'post': CommentPagesTests.post,
        }
        response = self.author_client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': CommentPagesTests.post.id
            }),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail',
                kwargs={'post_id': CommentPagesTests.post.id}
            )
        )
        self.assertEqual(
            Comment.objects.count(),
            self.comments_count + CommentPagesTests.ADDED_ENTRY
        )
        self.assertTrue(
            Comment.objects.filter(
                text='Test comment',
                author=CommentPagesTests.post.author,
                post=CommentPagesTests.post,
            ).exists()
        )

    def test_post_cannot_comments_anonymous(self):
        """Неавторизованный пользователь не может комментировать посты."""
        form_data = {
            'text': 'Test comment 2',
            'author': CommentPagesTests.author,
            'post': CommentPagesTests.post,
        }
        self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': CommentPagesTests.post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertNotEqual(
            Comment.objects.count(),
            self.comments_count + CommentPagesTests.ADDED_ENTRY
        )
        self.assertFalse(
            Comment.objects.filter(
                text='Test comment 2',
                author=CommentPagesTests.author,
                post=CommentPagesTests.post,
            ).exists()
        )


class FollowPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Author')
        cls.follower = User.objects.create_user(username='Follower')
        cls.not_follower = User.objects.create_user(username='NotFollower')
        cls.post = Post.objects.create(
            text='Test text',
            author=cls.author,
        )
        cls.post = Post.objects.create(
            text='Test text',
            author=cls.author,
        )

    def setUp(self):
        self.author_client = Client()
        self.follower_client = Client()
        self.not_follower_client = Client()
        self.author_client.force_login(FollowPagesTests.author)
        self.follower_client.force_login(FollowPagesTests.follower)
        self.not_follower_client.force_login(FollowPagesTests.not_follower)

    def test_authorized_can_follow_and_unfollow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок.
        """
        self.follower_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': FollowPagesTests.post.author}
            )
        )
        self.assertTrue(
            Follow.objects.filter(
                author=FollowPagesTests.post.author,
                user=FollowPagesTests.follower
            ).exists()
        )
        self.follower_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': FollowPagesTests.post.author}
            )
        )
        self.assertFalse(
            Follow.objects.filter(
                author=FollowPagesTests.post.author,
                user=FollowPagesTests.follower
            ).exists()
        )

    def test_new_post_appears_only_in_followers_list(self):
        """Новая запись пользователя появляется в ленте тех, кто на него
        подписан и не появляется в ленте тех, кто не подписан.
        """
        self.follower_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': FollowPagesTests.post.author}
            )
        )
        response_2 = self.follower_client.get(reverse('posts:follow_index'))
        response_3 = self.not_follower_client.get(reverse('posts:follow_index'))
        self.assertEqual(response_2.context['page_obj']
                         .paginator.page(1)
                         .object_list.count(), 2)
        self.assertEqual(response_3.context['page_obj']
                         .paginator.page(1)
                         .object_list.count(), 0)
