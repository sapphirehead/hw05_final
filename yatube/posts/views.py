from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from .models import Follow, Group, Post, User
from .forms import PostForm, CommentForm
from django.conf import settings


@cache_page(settings.CACHES_LIMIT)
def index(request):
    """Сохраняем в posts объекты модели Post,
    отсортированные по полю pub_date по убыванию.
    """
    posts_list = Post.objects.all()
    paginator = Paginator(posts_list, settings.PAGES_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """View-функция для страницы сообщества.
    Страница с информацией о постах отфильтрованных по группам.
    Принимает параметр slug из path()
    """
    groups_list = get_object_or_404(Group, slug=slug)
    posts_list = groups_list.posts.all()
    paginator = Paginator(posts_list, settings.PAGES_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': groups_list,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """View-функция для отображения профиля пользователя.
    Принимает параметр username из path()
    """
    author = get_object_or_404(User, username=username)
    posts_list = Post.objects.select_related('author').filter(author=author)
    paginator = Paginator(posts_list, settings.PAGES_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following = False
    if request.user.is_authenticated:
        following = author.following.filter(user=request.user).exists()
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """View-функция для отображения отдельного поста пользователя.
    Принимает порядковый номер поста из path()
    """
    post = get_object_or_404(Post, id=post_id)
    posts_count = Post.objects.select_related('author').filter(
        author=post.author
    ).count()
    comments = post.comments.select_related('author')
    form = CommentForm(
        request.POST or None,
    )
    context = {
        'post': post,
        'comments': comments,
        'form': form,
        'posts_count': posts_count,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """View-функция для создания отдельного поста пользователя."""
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()
        return redirect("posts:profile", username=post.author)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """View-функция для редактирования отдельного поста пользователя.
    Принимает порядковый номер поста из path()
    """
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect("posts:post_detail", post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id=post_id)
    context = {
        'form': form,
        'post': post,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    """Добавляет посту комментарий текущего пользователя."""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Выводит посты авторов, на которых подписан текущий пользователь."""
    posts_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts_list, settings.PAGES_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Осуществляет подписку на автора, записывая в БД."""
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.update_or_create(author=author, user=request.user)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    """Аннулирует подписку на автора, удаляя запись БД"""
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(author=author, user=request.user)
    if follow.exists():
        follow.delete()
    return redirect('posts:profile', username)
