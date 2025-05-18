from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.documents import Account
from .documents import Post, Comment, Group, Friendship, FriendRequest
from mongoengine.queryset.visitor import Q
from bson import ObjectId
from workouts.models import WorkoutLog
from dashboard.models import WeightLog
from goals.models import FitnessGoal
from .models import Challenge
from django.db.models import Max
from django.contrib.auth import get_user_model

@login_required
def social_hub(request):
    if not request.user.is_authenticated:
        return redirect('login')

    user_doc = Account.objects.get(username=request.user.username)

    search_results = []
    incoming_requests = FriendRequest.objects(receiver=user_doc, status='pending')
    outgoing_requests = FriendRequest.objects(sender=user_doc, status='pending')
    request_message = ""  # message to show in template

    friendships = Friendship.objects(user=user_doc)
    friend_ids = [friendship.friend.id for friendship in friendships]
    friends = Account.objects(id__in=friend_ids)

    posts = Post.objects(author__in=[user_doc] + [friendship.friend for friendship in friendships]).order_by('-created_at')
    groups = Group.objects(members=user_doc)
    group_search_results = []
    group_message = ""

    
    if request.method == 'POST':
        if 'comment_post' in request.POST:
            post_id = request.POST.get('post_id')
            content = request.POST.get('comment_content')
            post = Post.objects(id=post_id).first()
            if post and content:
                comment = Comment(post=post, author=user_doc, content=content)
                try:
                    comment.save()
                    print("Comment saved successfully!")
                except Exception as e:
                    print("Error saving comment:", e)
        elif 'like_post' in request.POST:
            post_id = request.POST['post_id']
            try:
                post = Post.objects.get(id=ObjectId(post_id))

                # Toggle the like
                if user_doc in post.likes:  # Checks if the user is already in the likes list
                    post.likes.remove(user_doc)  # Unlike
                    post.like_count -= 1  # Decrease the like count
                else:
                    post.likes.append(user_doc)  # Like
                    post.like_count += 1  # Increase the like count

                post.save()  # Save the updated post

            except Post.DoesNotExist:
                print("Post not found.")
        elif 'search_user' in request.POST:
            query = request.POST['search_query']
            friendships = Friendship.objects(user=user_doc)
            friend_ids = [friendship.friend.id for friendship in friendships]

            # Search users by username, exclude friends AND yourself
            search_results = Account.objects(username__icontains=query).filter(
                id__nin=friend_ids + [user_doc.id]
            )

        elif 'send_request' in request.POST:
            target_id = request.POST['target_id']
            try:
                target_user = Account.objects.get(id=ObjectId(target_id))
                existing_request = FriendRequest.objects(
                    (Q(sender=user_doc) & Q(receiver=target_user)) |
                    (Q(sender=target_user) & Q(receiver=user_doc))
                ).first()

                if not existing_request:
                    FriendRequest(sender=user_doc, receiver=target_user).save()
                    request_message = f"Friend request sent to {target_user.username}."
                else:
                    request_message = f"You have already sent a friend request to {target_user.username}."
            except Exception as e:
                print("Send request error:", e)
                request_message = "Something went wrong sending the friend request."

        elif 'accept_request' in request.POST:
            req_id = request.POST['request_id']
            try:
                fr = FriendRequest.objects.get(id=ObjectId(req_id), receiver=user_doc)
                fr.status = 'accepted'
                fr.save()
                Friendship(user=user_doc, friend=fr.sender).save()
                Friendship(user=fr.sender, friend=user_doc).save()
            except Exception as e:
                print("Accept request error:", e)

        elif 'reject_request' in request.POST:
            req_id = request.POST['request_id']
            try:
                fr = FriendRequest.objects.get(id=ObjectId(req_id), receiver=user_doc)
                fr.status = 'rejected'
                fr.save()
            except Exception as e:
                print("Reject request error:", e)
        elif 'create_post' in request.POST:  # <-- ADD THIS BLOCK
            content = request.POST.get('post_content')
            if content:
                new_post = Post(author=user_doc, content=content)
                new_post.save()

    comments_by_post = {}
    for post in posts:
        comments = Comment.objects(post=post)
        comments_by_post[post.id] = comments

    if request.method == 'POST':
        if 'search_group' in request.POST:
            group_query = request.POST['group_query']
            group_search_results = Group.objects(title__icontains=group_query).filter(members__ne=user_doc)

        elif 'join_group' in request.POST:
            group_id = request.POST['group_id']
            group = Group.objects(id=ObjectId(group_id)).first()
            if group and user_doc not in group.members:
                group.members.append(user_doc)
                group.save()
                group_message = f"You joined the group: {group.title}"
            else:
                group_message = "You are already in this group."

        elif 'create_group' in request.POST:
            group_title = request.POST['group_title']
            if not Group.objects(title=group_title).first():  # Prevent duplicate names
                group = Group(title=group_title, members=[user_doc])
                group.save()
                group_message = f"Group '{group_title}' created and joined!"
            else:
                group_message = "A group with this name already exists."
        elif 'leave_group' in request.POST:
            group_id = request.POST['group_id']
            group = Group.objects(id=ObjectId(group_id)).first()
            if group and user_doc in group.members:
                if group.creator != user_doc:
                    group.members.remove(user_doc)
                    group.save()
                    group_message = f"You left the group: {group.title}"
                else:
                    group_message = "You cannot leave a group you created. You can delete it instead."

        elif 'delete_group' in request.POST:
            group_id = request.POST['group_id']
            group = Group.objects(id=ObjectId(group_id)).first()
            if group and group.creator == user_doc:
                group.delete()
                group_message = f"The group '{group.title}' has been deleted."



    return render(request, 'social/social_hub.html', {
        'search_results': search_results,
        'incoming_requests': incoming_requests,
        'outgoing_requests': outgoing_requests,
        'posts': posts,
        'comments_by_post': comments_by_post,
        'groups': groups,
        'friends': friends,
        'request_message': request_message,
        'group_search_results': group_search_results,
        'group_message': group_message,
        'user': user_doc,
    })



@login_required
def add_friend(request, friend_id):
    friend = get_object_or_404(Account, id=friend_id)
    account = request.user
    if friend not in account.friends:
        account.friends.append(friend)
        account.save()
    return redirect('social_hub')

@login_required
def join_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    account = request.user
    if account not in group.members:
        group.members.append(account)
        group.save()
    return redirect('group_feed', group_id=group_id)

@login_required
def group_feed(request, group_id):
    try:
        group = Group.objects.get(id=ObjectId(group_id))
    except Group.DoesNotExist:
        return redirect('social_hub')  # If group doesn't exist

    user_doc = Account.objects.get(username=request.user.username)
    if user_doc not in group.members:
        return redirect('social_hub')  # Only members can view

    # Pass the list of members to the template
    members = group.members

    return render(request, 'social/group_feed.html', {
        'group': group,
        'members': members,
    })



@login_required
def create_post(request, group_id=None):
    if request.method == 'POST':
        content = request.POST['content']
        account = request.user
        group = Group.objects(id=group_id).first() if group_id else None

        post = Post(author=account, content=content, group=group)
        post.save()

        return redirect('group_feed', group_id=group_id) if group else redirect('social_hub')

    return render(request, 'social/create_post.html')

@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = request.user

    # Check if the user already liked the post
    if user in post.likes:
        # Remove the like (unlike)
        post.likes.remove(user)
    else:
        # Add a like
        post.likes.append(user)

    # Save the updated post object
    post.save()

    return redirect('social_hub')

@login_required
def add_comment(request):
    if request.method == 'POST':
        post_id = request.POST.get('post_id')
        content = request.POST.get('comment_content')
        post = Post.objects(id=post_id).first()
        if post and content:
            comment = Comment(author=request.user, post=post, content=content)
            comment.save()
    return redirect('social_hub')

@login_required
def join_challenge(request, challenge_id):
    challenge = get_object_or_404(Challenge, id=challenge_id)
    user_id = request.user.id
    if str(user_id) not in challenge.members:
        challenge.members[str(user_id)] = 0
        challenge.save()
    return redirect('challenges')

@login_required
def leave_challenge(request, challenge_id):
    challenge = get_object_or_404(Challenge, id=challenge_id)
    user_id = str(request.user.id)
    if user_id in challenge.members:
        del challenge.members[user_id]
        challenge.save()
    return redirect('challenges')

User = get_user_model()

@login_required
def leaderboard(request):
    challenges = Challenge.objects.all()

    for challenge in challenges:
        for user_id, progress in list(challenge.members.items()):
            try:
                user = User.objects.get(id=int(user_id))

                if challenge.challenge_type == "active_days":
                    challenge.members[user_id] = {
                        "username": user.username,
                        "progress": WorkoutLog.objects.filter(user=user).values('date').distinct().count()
                    }
                elif challenge.challenge_type == "weight_lifted":
                    challenge.members[user_id] = {
                        "username": user.username,
                        "progress": WorkoutLog.objects.filter(user=user).aggregate(max_weight=Max('weight'))['max_weight'] or 0
                    }
            except (User.DoesNotExist, ValueError):
                # Remove invalid or non-existent users from the members field
                del challenge.members[user_id]
                continue

        sorted_members = dict(
            sorted(challenge.members.items(), key=lambda item: item[1]['progress'], reverse=True)
        )
        challenge.members = sorted_members
        challenge.save()

    current_user = str(request.user.id)
    # Pass the challenges to the template
    return render(request, 'social/challenges.html', {
        'challenges': challenges,
        'current_user' : current_user
    })