from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings

from .forms import PostForm, CommentForm
from .models import Post, Group, User, Follow


def paginator(request, post_list):
    _paginator = Paginator(post_list, settings.LIMIT_ITEMS)
    page_number = request.GET.get('page')
    page_obj = _paginator.get_page(page_number)
    return page_obj


def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.select_related('author', 'group').all()
    context = {
        'index': True,
        'page_obj': paginator(request, post_list),
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author').all()
    context = {
        'group': group,
        'page_obj': paginator(request, post_list),
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    user = get_object_or_404(User, username=username)
    post_list = user.posts.select_related('group').all()
    following_status = (request.user.is_authenticated
                        and Follow.objects.filter(
                            user=request.user,
                            author=user).exists())
    show_follow_button = True
    if request.user == user or not request.user.is_authenticated:
        show_follow_button = False
    context = {
        'show_follow_button': show_follow_button,
        'following_status': following_status,
        'consumer': user,
        'page_obj': paginator(request, post_list),
    }
    return render(request, template, context)


def post_detail(request, post_id):
    form = CommentForm()
    post = get_object_or_404(
        Post.objects.select_related('author', 'group'),
        id=post_id)
    comments = post.comments.all()
    context = {
        'form': form,
        'post': post,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None, )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user.username)
    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'is_edit': True,
        'id': post_id,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    post_list = Post.objects.filter(
        author__following__user=request.user)  # не ясно
    context = {
        'follow': True,
        'page_obj': paginator(request, post_list),
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    template = 'posts/index.html'
    author = get_object_or_404(User, username=username)
    if request.user != author:
        # не ясно
        Follow.objects.get_or_create(user=request.user, author=author)
    return render(request, template)


@login_required
def profile_unfollow(request, username):
    template = 'posts/index.html'
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return render(request, template)
