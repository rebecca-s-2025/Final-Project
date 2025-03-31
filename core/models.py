from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from taggit.managers import TaggableManager
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _

# Constants
MODE = (
    ('Active', 'Active'),
    ('Deactivated', 'Deactivated'),
    ('Trash', 'Trash'),
)

GENDER = (
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
)

# Custom Manager to filter active objects.
class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(mode='Active')

class BaseModel(models.Model):
    created_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        editable=False,
        related_name='%(class)s_created'
    )
    modified_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        editable=False,
        related_name='%(class)s_modified'
    )
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)
    mode = models.CharField(max_length=30, default='Active', choices=MODE)

    objects = models.Manager()      # Default manager.
    active = ActiveManager()          # Manager for active objects.

    class Meta:
        abstract = True

# -- Category --
class Category(BaseModel):
    CATEGORY_TYPES = (
        ('FORUM', 'Forum'),
        ('NOTE', 'Student Note'),
        ('BOTH', 'Both'),
    )
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category_type = models.CharField(max_length=5, choices=CATEGORY_TYPES, default='BOTH')
    tags = TaggableManager(blank=True)

    def __str__(self):
        return self.name

# -- Role --
class Role(BaseModel):
    ROLE_TYPES = (
        ('U', 'User'),
        ('A', 'Admin'),
        ('O', 'Owner'),
    )
    
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    role_type = models.CharField(max_length=1, choices=ROLE_TYPES, default='U')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Role")
        verbose_name_plural = _("Roles")

# -- User Manager & User --

class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        default_role, _ = Role.objects.get_or_create(
            name='User',
            defaults={
                'role_type': 'U',
                'description': 'Regular User',
                'mode': 'Active'
            }
        )
        extra_fields.setdefault('role', default_role)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password, **extra_fields):
        owner_role, _ = Role.objects.get_or_create(
            name="Owner",
            defaults={
                'role_type': 'O',
                'description': 'System Owner',
                'mode': 'Active'
            }
        )
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', owner_role)
        return self.create_user(username=username, email=email, password=password, **extra_fields)
    

class User(BaseModel, AbstractUser):
    first_name = models.CharField(_("First Name"), max_length=255)
    last_name = models.CharField(_("Last Name"), max_length=255)
    gender = models.CharField(_("Gender"), max_length=30, choices=GENDER)
    email = models.EmailField(_("Email Address"), unique=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
    photo = models.ImageField(upload_to='users/photos/', blank=True)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    points = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    public_profile = models.BooleanField(default=True)
    joined_categories = models.ManyToManyField(Category, blank=True)
    liked_posts = models.ManyToManyField('ForumPost', through='PostLike', related_name='liked_by')
    liked_comments = models.ManyToManyField('Comment', through='CommentLike', related_name='liked_by')
    liked_notes = models.ManyToManyField('StudentNote', through='NoteLike', related_name='liked_by')
    muted_posts = models.ManyToManyField(
        'ForumPost', 
        through='MutedPost', 
        through_fields=('user', 'post'),
        related_name='muting_users'
    )
    notification_preferences = models.JSONField(default=dict)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name', 'gender']
    objects = UserManager()

    @property
    def required_points(self):
        return int(10 * (1.5 ** (self.level - 1)))

    def update_level(self):
        level = 1
        required = 10

        while self.points >= required:
            level += 1
            required = int(10 * (1.5 ** (level - 1)))

        self.level = level
        self.save(update_fields=['level'])

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")


# -- ForumPost --
class ForumPost(BaseModel):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        limit_choices_to={'category_type__in': ['FORUM', 'BOTH']}
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_forum_posts')
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='forum/images/', blank=True, null=True)
    tags = TaggableManager(blank=True)
    anonymous = models.BooleanField(default=False)
    reply_count = models.IntegerField(default=0)
    removed = models.BooleanField(default=False)
    removal_reason = models.TextField(blank=True)
    reports = GenericRelation('Report')
    notifications = GenericRelation('Notification')
    comments = GenericRelation('Comment', related_query_name='forum_posts')

    def total_likes(self):
        return self.liked_by.count()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("Forum Post")
        ordering = ['-created_on']

# -- Comment --
class Comment(BaseModel):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    anonymous = models.BooleanField(default=False)
    removed = models.BooleanField(default=False)
    removal_reason = models.TextField(blank=True)
    reports = GenericRelation('Report')
    likes = GenericRelation('CommentLike')

    def __str__(self):
        # Return a truncated comment
        return f"Comment by {self.author.username}: {self.content[:30]}..."

    class Meta:
        verbose_name = _("Comment")
        ordering = ['created_on']

# -- StudentNote --
class StudentNote(BaseModel):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        limit_choices_to={'category_type__in': ['NOTE', 'BOTH']}
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_student_notes')
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    file = models.FileField(
        upload_to='notes/files/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'png', 'jpeg'])]
    )
    tags = TaggableManager(blank=True)
    removed = models.BooleanField(default=False)
    removal_reason = models.TextField(blank=True)
    reports = GenericRelation('Report')
    comments = GenericRelation('Comment', related_query_name='student_notes')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("Student Note")
        ordering = ['-created_on']

# -- Textbook --
class Textbook(BaseModel):
    title = models.CharField(max_length=200)
    isbn = models.CharField(max_length=13)
    stock = models.PositiveIntegerField(default=0)
    locations = models.ManyToManyField('DropLocation')
    relevant_categories = models.ManyToManyField(Category)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("Textbook")
        ordering = ['title']

# -- TextbookRequest --
class TextbookRequest(BaseModel):
    STATUS_CHOICES = [
        ('P', 'Pending'),
        ('S', 'Dropped'),
        ('A', 'Approved'),
        ('D', 'Denied'),
        ('C', 'Completed'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    textbook = models.ForeignKey(Textbook, on_delete=models.CASCADE)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P', db_index=True)
    location = models.ForeignKey('DropLocation',  on_delete=models.CASCADE)
    fulfillment_date = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Request by {self.user.username} for {self.textbook.title}"

    class Meta:
        verbose_name = _("Textbook Request")
        ordering = ['-created_on']
        
    def save(self, *args, **kwargs):
        if self.status == 'A' and self.textbook.stock > 0:
            self.textbook.stock -= 1
            self.textbook.save()
            TextbookStockHistory.objects.create(
                textbook=self.textbook,
                admin=User.objects.get(is_staff=True),
                old_stock=self.textbook.stock + 1,
                new_stock=self.textbook.stock
            )
        super().save(*args, **kwargs)

# -- DropLocation --
class DropLocation(BaseModel):
    name = models.CharField(max_length=200)
    address = models.TextField()
    lat = models.FloatField()
    lng = models.FloatField()
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Drop Location")
        ordering = ['name']

# -- Report --

class Report(BaseModel):
    CONTENT_TYPES = [
        ('POST', 'Forum Post'),
        ('COMMENT', 'Comment'),
        ('NOTE', 'Student Note'),
        ('USER', 'User'),
    ]
    reporter = models.ForeignKey(User, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    reason = models.TextField()
    status = models.CharField(max_length=1, choices=[('U', 'Unresolved'), ('R', 'Resolved')], default='U', db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True, null=True, verbose_name="Resolution Notes")

    def __str__(self):
        return f"Report: {self.reason[:20]}..."

    class Meta:
        verbose_name = _("Report")
        ordering = ['-created_on']

# -- Notification --
class Notification(BaseModel):
    NOTIFICATION_TYPES = [
        ('LEVEL_UP', 'Level Up'),
        ('REPLY', 'Post Reply'),
        ('REQUEST_UPDATE', 'Request Update'),
        ('REPORT_RESOLVED', 'Report Resolved'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    read = models.BooleanField(default=False)
    link = models.URLField(blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey()

    def __str__(self):
        return f"{self.notification_type}: {self.message[:30]}"

    class Meta:
        verbose_name = _("Notification")
        ordering = ['-created_on']

# -- Donation --
class Donation(BaseModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    receipt_email = models.EmailField()
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_id = models.CharField(max_length=100)

    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Donation of {self.amount} by {self.first_name} {self.last_name}"

    class Meta:
        verbose_name = _("Donation")
        ordering = ['-created_on']


# -- Through Models --

class PostLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} liked {self.post.title}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.post.author.points += 1
        self.post.author.update_level()
        self.post.author.save()

    
class CommentLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} liked comment: {self.comment.content[:20]}..."
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.comment.author.points += 1 
        self.comment.author.save()

class NoteLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    note = models.ForeignKey(StudentNote, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} liked note {self.note.title}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.note.author.points += 1
        self.note.author.save()

class MutedPost(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_mutes')
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='post_mutes')
    mute_duration = models.IntegerField()  # Duration in days

    def __str__(self):
        return f"{self.user.username} muted {self.post.title} for {self.mute_duration} days"

class TextbookStockHistory(models.Model):
    textbook = models.ForeignKey(Textbook, on_delete=models.CASCADE)
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    old_stock = models.IntegerField()
    new_stock = models.IntegerField()
    modified_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.textbook.title}: {self.old_stock} -> {self.new_stock}"
    

class TextbookDrop(BaseModel):
    textbook_title = models.CharField(max_length=200)
    textbook_isbn = models.CharField(max_length=13)
    drop_date = models.DateTimeField()
    remarks = models.TextField(blank=True)
    # The drop location will be set separately via the view.
    drop_location = models.ForeignKey(DropLocation, on_delete=models.CASCADE, related_name='drops')
    
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('COLLECTED', 'Collected'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    
    def __str__(self):
        return f"{self.textbook_title} at {self.drop_location.name}"
    
    class Meta:
        verbose_name = _("Textbook Drop")
        ordering = ['-created_on']
    
    
class ContactMessage(models.Model):
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} ({self.submitted_at.strftime('%Y-%m-%d')})"