from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.utils.http import urlencode
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render, redirect
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

from .models import *
from .forms import *

# Utility decorator and function
def admin_required(view_func):
    decorated_view_func = user_passes_test(
        lambda u: u.role and u.role.role_type in ['A', 'O'],
        login_url='/'
    )(view_func)
    return decorated_view_func

def is_admin(user):
    return user.role and user.role.role_type in ['A', 'O']

# --------------------------
# Authentication Views
# --------------------------

def register(request):
    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Force default role if not provided
            if not user.role:
                user.role = Role.objects.get(name='User')
            user.save()
            messages.success(request, "Registration successful. Please log in.")
            return redirect('login')
    else:
        form = CustomUserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


# --------------------------
# Profile Views
# --------------------------


@login_required
def view_profile(request):
    # Correct usage of related names
    user = request.user
    recent_notes = user.user_student_notes.order_by('-created_on')[:5]
    recent_posts = user.user_forum_posts.order_by('-created_on')[:5]

    context = {
        'user': user,
        'recent_posts': recent_posts,
        'recent_notes': recent_notes,
        'likes': user.points,
    }

    return render(request, 'profile/view_profile.html', context)

@login_required
def update_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('view_profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'profile/update_profile.html', {'form': form})

def public_profile(request, username):
    user = get_object_or_404(User, username=username)
    user = request.user
    recent_notes = user.user_student_notes.order_by('-created_on')[:5]
    recent_posts = user.user_forum_posts.order_by('-created_on')[:5]

    context = {
        'user': user,
        'recent_posts': recent_posts,
        'recent_notes': recent_notes,
        'likes': user.points,
        'public_user': user
    }
    
    return render(request, 'profile/public_profile.html', context)


# --------------------------
# Core Views
# --------------------------

def home(request):
    context_data = dict()
    total_donations = Donation.objects.aggregate(total=Sum('amount'))['total'] or 0
    context_data['total_donations'] = total_donations
    return render(request, 'core/home.html', context=context_data)

def about(request):
    return render(request, 'core/about.html')

# --------------------------
# Forum Views
# --------------------------
def forum_category_list(request):
    categories = Category.objects.filter(category_type__in=['FORUM', 'BOTH']).annotate(
        post_count=Count('forumpost')
    )
    return render(request, 'forum/forum_category_list.html', {'categories': categories})


def forum_post_list(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    posts = ForumPost.objects.filter(category=category, removed=False).order_by('-created_on')
    
    tag_filter = request.GET.get('tag', '').strip()
    search_query = request.GET.get('q', '').strip()
    
    if tag_filter:
        posts = posts.filter(tags__name__iexact=tag_filter)
    if search_query:
        posts = posts.filter(Q(title__icontains=search_query) | Q(content__icontains=search_query))
    
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    recent_posts = ForumPost.objects.filter(removed=False).order_by('-created_on')
    
    # Build dictionary mapping post id to already_reported (True/False) for current user.
    report_status = {}
    if request.user.is_authenticated:
        post_ctype = ContentType.objects.get_for_model(ForumPost)
        for post in page_obj:
            report_status[post.id] = Report.objects.filter(
                reporter=request.user, content_type=post_ctype, object_id=post.id
            ).exists()
        
    context = {
        'category': category,
        'page_obj': page_obj,
        'tags': category.tags.all(),
        'search_query': search_query,
        'report_status': report_status,
        'recent_posts': recent_posts,
    }
    return render(request, 'forum/post_list.html', context)


@login_required
def forum_post_create(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        form = ForumPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.category = category
            post.created_by = request.user
            post.save()
            form.save_m2m()  # Save many-to-many data (tags)
            return redirect('forum_post_detail', post_id=post.id)
    else:
        form = ForumPostForm(initial={'category': category})
    return render(request, 'forum/post_create.html', {'form': form, 'category': category})


def forum_post_detail(request, post_id):
    post = get_object_or_404(ForumPost, id=post_id)
    comments = post.comments.filter(removed=False).order_by('created_on')
    
    # Check if the current user has reported the post
    post_ctype = ContentType.objects.get_for_model(ForumPost)
    already_reported = False
    if request.user.is_authenticated:
        already_reported = Report.objects.filter(
            reporter=request.user,
            content_type=post_ctype,
            object_id=post.id
        ).exists()
    
    # Build a dictionary for comment report status for each comment
    comment_ctype = ContentType.objects.get_for_model(Comment)
    comment_report_status = {}
    
    
    if request.user.is_authenticated:
        for comment in comments:
            comment_report_status[comment.id] = Report.objects.filter(
                reporter=request.user,
                content_type=comment_ctype,
                object_id=comment.id
            ).exists()
    
    if request.method == 'POST':
        # Process new comment submission
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.author = request.user
            comment.created_by = request.user
            comment.content_object = post
            comment.save()
            return redirect('forum_post_detail', post_id=post.id)
    else:
        comment_form = CommentForm()
    
    recent_posts = ForumPost.objects.filter(removed=False).order_by('-created_on')[:3]
    
    context = {
        'post': post,
        'recent_posts': recent_posts,
        'comments': comments,
        'comment_form': comment_form,
        'user_can_moderate': is_admin(request.user) if request.user.is_authenticated else False,
        'already_reported': already_reported,
        'comment_report_status': comment_report_status,
    }
    return render(request, 'forum/post_detail.html', context)


@login_required
def like_post(request, post_id):
    post = get_object_or_404(ForumPost, id=post_id)
    # Prevent author from liking their own post.
    if post.author == request.user:
        return JsonResponse({'error': "You can't like your own post."}, status=403)
    
    try:
        # If the like already exists, remove it (dislike)
        like = PostLike.objects.get(user=request.user, post=post)
        like.delete()
    except PostLike.DoesNotExist:
        # Otherwise, create a new like
        PostLike.objects.create(user=request.user, post=post)
        # Increase the author's points (and check for level-up if needed)
        post.author.points += 1
        post.author.save()
    
    # Return the updated like count
    return JsonResponse({'likes_count': post.liked_by.count()})


@login_required
def like_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    # Prevent the comment's author from liking their own comment.
    if comment.author == request.user:
        return JsonResponse({'error': "You can't like your own comment."}, status=403)
    
    try:
        # If the like exists, remove it (dislike)
        like = CommentLike.objects.get(user=request.user, comment=comment)
        like.delete()
    except CommentLike.DoesNotExist:
        # Otherwise, create a new like
        CommentLike.objects.create(user=request.user, comment=comment)
        # Increase the comment author's points
        comment.author.points += 1
        comment.author.update_level()
        comment.author.save()
    
    # Return the updated like count
    return JsonResponse({'likes_count': comment.likes.count()})
    
# --------------------------
# Student Notes Views
# --------------------------
def notes_category_list(request):
    categories = Category.objects.filter(category_type__in=['NOTE', 'BOTH']).annotate(
        note_count=Count('studentnote')
    )
    return render(request, 'notes/notes_category_list.html', {'categories': categories})


# 2. List Notes in a Category
def notes_list(request, category_id):
    category = get_object_or_404(Category, id=category_id, category_type__in=['NOTE', 'BOTH'])
    notes = StudentNote.objects.filter(category=category, removed=False).order_by('-created_on')
    
    tag_filter = request.GET.get('tag', '').strip()
    search_query = request.GET.get('q', '').strip()
    
    if tag_filter:
        notes = notes.filter(tags__name__iexact=tag_filter)
    if search_query:
        notes = notes.filter(Q(title__icontains=search_query) | Q(content__icontains=search_query))
    
    paginator = Paginator(notes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    recent_posts = StudentNote.objects.filter(removed=False).order_by('-created_on')
    # Build dictionary mapping note id to already_reported status for current user.
    report_status = {}
    if request.user.is_authenticated:
        note_ctype = ContentType.objects.get_for_model(StudentNote)
        for note in page_obj:
            report_status[note.id] = Report.objects.filter(
                reporter=request.user, content_type=note_ctype, object_id=note.id
            ).exists()
    
    context = {
        'category': category,
        'page_obj': page_obj,
        'tags': category.tags.all(),
        'search_query': search_query,
        'report_status': report_status,
        'recent_posts': recent_posts,
    }
    return render(request, 'notes/notes_list.html', context)


# 3. Create a New Note in a Category
@login_required
def note_create(request, category_id):
    category = get_object_or_404(Category, id=category_id, category_type__in=['NOTE', 'BOTH'])
    if request.method == 'POST':
        data = request.POST.copy()
        data['category'] = category  
        
        form = StudentNoteForm(data, request.FILES)
        if form.is_valid():
            note = form.save(commit=False)
            note.author = request.user
            note.created_by = request.user
            note.category = category
            note.save()
            form.save_m2m()  # Save tags
            return redirect('note_detail', note_id=note.id)
    else:
        form = StudentNoteForm(initial={'category': category})
    return render(request, 'notes/note_create.html', {'form': form, 'category': category})


# 4. Note Detail View (with comments and comment submission)
def note_detail(request, note_id):
    note = get_object_or_404(StudentNote, id=note_id)
    comments = note.comments.filter(removed=False).order_by('created_on')
    
    # Check if the current user has reported the note
    note_ctype = ContentType.objects.get_for_model(StudentNote)
    already_reported = False
    if request.user.is_authenticated:
        already_reported = Report.objects.filter(
            reporter=request.user,
            content_type=note_ctype,
            object_id=note.id
        ).exists()
    
    
    recent_posts = StudentNote.objects.filter(removed=False).order_by('-created_on')[:3]
    
    # Build a dictionary for comment report status for each comment.
    comment_ctype = ContentType.objects.get_for_model(Comment)
    comment_report_status = {}
    if request.user.is_authenticated:
        for comment in comments:
            comment_report_status[comment.id] = Report.objects.filter(
                reporter=request.user,
                content_type=comment_ctype,
                object_id=comment.id
            ).exists()
    
    if request.method == 'POST':
        # Process new comment submission
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.author = request.user
            comment.created_by = request.user
            comment.content_object = note
            comment.save()
            return redirect('note_detail', note_id=note.id)
    else:
        comment_form = CommentForm()
    
    context = {
        'note': note,
        'comments': comments,
        'comment_form': comment_form,
        'user_can_moderate': is_admin(request.user) if request.user.is_authenticated else False,
        'already_reported': already_reported,
        'comment_report_status': comment_report_status,
        'recent_posts': recent_posts,
    }
    return render(request, 'notes/note_detail.html', context)

# 5. Like Note View (toggle like/dislike for note)
@login_required
def like_note(request, note_id):
    note = get_object_or_404(StudentNote, id=note_id)
    # Prevent author from liking their own note.
    if note.author == request.user:
        return JsonResponse({'error': "You can't like your own note."}, status=403)
    
    try:
        like = NoteLike.objects.get(user=request.user, note=note)
        like.delete()
    except NoteLike.DoesNotExist:
        NoteLike.objects.create(user=request.user, note=note)
        note.author.points += 1
        note.author.update_level()
        note.author.save()
    
    return JsonResponse({'likes_count': note.likes.count()})

# 6. Like Comment on Note View (toggle like/dislike for comment on note)
@login_required
def like_comment_note(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    # Prevent the comment's author from liking their own comment.
    if comment.author == request.user:
        return JsonResponse({'error': "You can't like your own comment."}, status=403)
    
    try:
        like = CommentLike.objects.get(user=request.user, comment=comment)
        like.delete()
    except CommentLike.DoesNotExist:
        CommentLike.objects.create(user=request.user, comment=comment)
        comment.author.points += 1
        comment.author.update_level()
        comment.author.save()
    
    return JsonResponse({'likes_count': comment.likes.count()})

# --------------------------
# Report System Views
# --------------------------

@login_required
def report_create(request, content_type, object_id):
    # Map content_type strings to models.
    content_model = {
        'post': ForumPost,
        'comment': Comment,
        'note': StudentNote,
        'user': User,
    }.get(content_type.lower())
    
    if not content_model:
        return redirect('home')
    
    content_object = get_object_or_404(content_model, id=object_id)
    
    # Check if a report from this user for this object already exists.
    ctype = ContentType.objects.get_for_model(content_model)
    if Report.objects.filter(reporter=request.user, content_type=ctype, object_id=object_id).exists():
        messages.error(request, "You have already reported this content.")
        # Redirect to a relevant page (for example, back to the content detail page)
        if content_type.lower() == 'post':
            return redirect('forum_post_detail', post_id=object_id)
        elif content_type.lower() == 'note':
            return redirect('student_note_detail', note_id=object_id)
        else:
            return redirect('home')
    
    if request.method == 'POST':
        data = request.POST.copy()
        data['object_id'] = object_id  # Ensure object_id is present in POST data.
        form = ReportForm(data)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.content_object = content_object
            report.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success', 'message': 'Report submitted successfully'})
            messages.success(request, 'Report submitted successfully')
            return redirect('home')
    else:
        form = ReportForm()
    
    return render(request, 'reports/create.html', {
        'form': form,
        'content_object': content_object
    })
    

@staff_member_required
def report_list(request):
    reports = Report.objects.filter(status='U').order_by('-created_on')
    return render(request, 'reports/list.html', {'reports': reports})

@staff_member_required
def report_resolve(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    if request.method == 'POST':
        form = AdminReportResolutionForm(request.POST, instance=report)
        if form.is_valid():
            resolved_report = form.save(commit=False)
            resolved_report.status = 'R'
            resolved_report.resolved_at = timezone.now()
            resolved_report.save()
            return redirect('report_list')
    else:
        form = AdminReportResolutionForm(instance=report)
    return render(request, 'reports/resolve.html', {'form': form, 'report': report})

# --------------------------
# Admin Dashboard & Management Views
# --------------------------
@staff_member_required
def admin_dashboard(request):
    stats = {
        'total_users': User.objects.count(),
        'active_requests': TextbookRequest.objects.filter(status='P').count(),
        'unresolved_reports': Report.objects.filter(status='U').count()
    }
    return render(request, 'admin/dashboard.html', {'stats': stats})

@staff_member_required
def admin_category_manage(request):
    categories = Category.objects.all().order_by('name')
    return render(request, 'admin/categories.html', {'categories': categories})

@staff_member_required
def admin_user_manage(request):
    users = User.objects.all().order_by('username')
    return render(request, 'admin/users.html', {'users': users})

# --------------------------
# Donation Views
# --------------------------
def donate(request):
    
    if request.method == 'POST':
        
        form = DonationForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.save()
            messages.success(request, "Thank you for your donation!")
            return redirect('donate')
    else:
        initial_data =  dict()
        if request.user.is_authenticated:
            initial_data['first_name'] = request.user.first_name
            initial_data['last_name'] = request.user.last_name
            initial_data['receipt_email'] = request.user.email
            
        form = DonationForm(initial=initial_data)
    return render(request, 'donations/donate-us.html', {'form': form})

def donation_success(request):
    return render(request, 'donations/success.html')

# --------------------------
# Textbook Management Views
# --------------------------
def browse_textbooks_requests(request):
    
    textbook_requests = TextbookRequest.objects.all().order_by('-created_on')
    query = request.GET.get('q', '')

    if query:
        textbook_requests = textbook_requests.filter(
            Q(textbook__title__icontains=query) |
            Q(textbook__isbn__icontains=query) |
            Q(location__name__icontains=query)
        )
    
    context = {
        'textbook_requests': textbook_requests,
    }
    return render(request, 'textbooks/text_books_requests_list.html', context)


@login_required
def fullfill_textbook_request(request, textbook_request_id):
    content_object = get_object_or_404(TextbookRequest, id=textbook_request_id)
    url = reverse('drop_textbook_form_update', args=[content_object.location.id])
    query_params = {}

    if content_object.textbook:
        query_params['textbook_id'] = content_object.textbook.id

    if query_params:
        url += '?' + urlencode(query_params)

    return redirect(url)


@login_required
def textbook_request(request):
    if request.method == 'POST':
        form = TextbookRequestForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data['title']
            isbn = form.cleaned_data['isbn']
            location = form.cleaned_data['location']
            # Get or create the textbook based on title and ISBN
            textbook, created = Textbook.objects.get_or_create(
                title=title,
                isbn=isbn,
                defaults={'stock': 0}  # adjust as needed
            )
            textbook_request = TextbookRequest.objects.create(
                user=request.user,
                textbook=textbook,
                location=location,
                status='P',
                created_by=request.user
            )
            Notification.objects.create(
                user=request.user,
                notification_type='REQUEST_UPDATE',
                message=f"Textbook request submitted: {textbook.title}"
            )
            return redirect('list_textbooks_requests')
    else:
        form = TextbookRequestForm()
    return render(request, 'textbooks/textbook_request_form.html', {'form': form})


@staff_member_required
def textbook_manage(request):
    textbooks = Textbook.objects.all().order_by('title')
    return render(request, 'textbooks/manage.html', {'textbooks': textbooks})

# --------------------------
# Textbook Drop Views
# --------------------------
def drop_textbook(request):
    locations = DropLocation.objects.all().order_by('name')
    return render(request, 'textbooks/drop_textbook.html', {'locations': locations})


def list_dropped_textbooks(request):
    if not request.user.is_authenticated:
        return redirect('drop_textbook')
    # Check if the user is an admin/owner (adjust the condition based on your role logic).
    if request.user.is_superuser or (request.user.role and request.user.role.role_type in ['A', 'O']):
        drops = TextbookDrop.objects.all().order_by('-drop_date')
    else:
        drops = TextbookDrop.objects.filter(created_by=request.user).order_by('-drop_date')
    
    query = request.GET.get('q', '')

    if query:
        drops = drops.filter(
            Q(textbook_title__icontains=query) |
            Q(textbook_isbn__icontains=query) |
            Q(drop_location__name__icontains=query)
        )
    
    context = {
        'drops': drops,
    }
    return render(request, 'textbooks/dropped_textbooks_list.html', context)


@login_required
def drop_textbook_form(request, location_id:None):
    # Check if a location_id was provided in the GET parameters
    initial_data = {}
    if location_id:
        try:
            location = DropLocation.objects.get(id=location_id)
            initial_data['drop_location'] = location
        except DropLocation.DoesNotExist:
            pass  # No initial location will be set if the provided id is invalid
        
    # Optional query param
    textbook_id = request.GET.get('textbook_id')
    if textbook_id:
        try:
            textbook = Textbook.objects.get(id=int(textbook_id))
            initial_data['textbook_title'] = textbook.title
            initial_data['textbook_isbn'] = textbook.isbn
        except Textbook.DoesNotExist:
            pass


    form = TextbookDropForm(request.POST or None, initial=initial_data)
    
    if request.method == 'POST':
        if form.is_valid():
            drop = form.save(commit=False)
            drop.created_by = request.user
            drop.save()
            return redirect('list_dropped_textbooks')  # Adjust URL name as needed.
    
    return render(request, 'textbooks/drop_textbook_form.html', {'form': form})


# --------------------------
# Mark All Notification Read
# --------------------------

@require_POST
@login_required
def mark_all_notifications_read(request):
    request.user.notification_set.filter(read=False).update(read=True)
    return JsonResponse({'status': 'ok'})


# --------------------------
# Contact Us
# --------------------------

def contact_form_submit(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        message = request.POST.get('message')
        
        # Save to DB
        ContactMessage.objects.create(
            email=email,
            phone=phone,
            address=address,
            message=message
        )
        context = {
            'email': email,
            'phone': phone,
            'address': address,
            'message': message,
            'domain': request.get_host(),
            'protocol': 'https' if request.is_secure() else 'http',
        }
        subject = "Thanks for contacting EducAid!"
        html_content = render_to_string('profile/contact_confirmation_email.html', context)
        text_content = strip_tags(html_content)

        email_msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [email])
        email_msg.attach_alternative(html_content, "text/html")
        email_msg.send()
        messages.success(request, "Thanks for contacting us")

    return redirect('home')

# --------------------------
# Error Handlers
# --------------------------
def handle_404(request, exception):
    return render(request, 'errors/404.html', status=404)

def handle_500(request):
    return render(request, 'errors/500.html', status=500)