from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm
from .helpers import paginate


@cache_page(20, key_prefix='index_page')
def index(request):
    posts = Post.objects.all().order_by('-pub_date')
    page_obj = paginate(request, posts)
    context = {
        'page_obj': page_obj,
        'show_link': True,
    }
    return render(request, 'posts/index.html', context)


def group_list(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all().order_by('-pub_date')
    page_obj = paginate(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    template = 'posts/profile.html'
    page_obj = paginate(request, posts)
    posts_count = posts.count()
    user_auth = request.user.is_authenticated
    if user_auth and Follow.objects.filter(user=request.user,
                                           author=author).exists():
        following = True
    else:
        following = False
    context = {
        'page_obj': page_obj,
        'author': author,
        'posts_count': posts_count,
        'show_link': False,
        'following': following
    }
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    posts_count = post.author.posts.count()
    comments = Comment.objects.filter(post=post)
    comment_form = CommentForm()
    context = {
        'post': post,
        'posts_count': posts_count,
        'comments': comments,
        'comment_form': comment_form
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user)
    else:
        form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post.id)

    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)

    is_edit = True
    context = {
        'form': form,
        'post': post,
        'is_edit': is_edit
    }

    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post.id)


@login_required
def follow_index(request):
    user = request.user
    following = Follow.objects.filter(user=user).values_list('author_id',
                                                             flat=True)
    posts = Post.objects.filter(author__in=following).order_by('-pub_date')
    page_obj = paginate(request, posts)
    context = {
        'page_obj': page_obj,
        'show_link': True,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)

    if not Follow.objects.filter(
            user=user,
            author=author
    ).exists():
        if user != author:
            Follow.objects.create(user=user, author=author)

    return redirect('posts:profile', username=author)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)
