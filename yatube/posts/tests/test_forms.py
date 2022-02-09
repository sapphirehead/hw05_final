import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from ..models import Comment, Group, Post, User
from django.urls import reverse


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ADDED_ENTRY = 1
        cls.author = User.objects.create_user(username='UserAndAuthor')
        cls.group = Group.objects.create(
            title='Test title',
            slug=cls.author,
            description='Test description'
        )
        cls.post = Post.objects.create(
            text='Test text1',
            author=cls.author,
            group=cls.group
        )
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(PostFormTests.author)
        self.posts_count = Post.objects.count()
        self.comments_count = Comment.objects.count()

    def test_create_form(self):
        """Валидная форма создает запись в Post."""
        form_data = {
            'text': 'Text text2',
            'author': PostFormTests.author,
            'group': PostFormTests.group.id,
            'image': PostFormTests.uploaded,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:profile', kwargs={'username': self.author}
            )
        )
        self.assertEqual(
            Post.objects.count(), self.posts_count + PostFormTests.ADDED_ENTRY
        )
        self.assertTrue(
            Post.objects.filter(
                text='Text text2',
                author=self.author,
                group=self.group,
                image='posts/test.gif',
            ).exists()
        )

    def test_edit_form(self):
        """Валидная форма редактирует запись в Post."""
        post = Post.objects.get(
            text='Test text1',
            author=PostFormTests.author,
            group=PostFormTests.group,
        )
        form_data = {
            'text': 'Test text1 edited',
            'author': PostFormTests.author,
            'group': PostFormTests.group.id,
        }
        response = self.author_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': post.id}
            )
        )
        self.assertEqual(Post.objects.count(), self.posts_count)
        self.assertTrue(
            Post.objects.filter(
                text='Test text1 edited',
                author=self.author,
                group=self.group,
            ).exists()
        )
