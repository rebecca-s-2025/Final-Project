from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from taggit.forms import TagWidget, TagField
from django.core.exceptions import ValidationError
from .models import (
    User, ForumPost, StudentNote, TextbookRequest, Comment,
    Category, Textbook, DropLocation, Report,
    Donation, GENDER, TextbookDrop
)

# --------------------------
# User Management Forms
# --------------------------

class CustomUserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'gender']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered")
        return email

class AdminUserManagementForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['role', 'is_active', 'public_profile']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
        }

        
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'gender', 'email', 'photo', 'bio', 'location']
        widgets = {
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'bio': forms.TextInput(attrs={'class': 'form-control'}),
        }

# --------------------------
# Content Creation Forms
# --------------------------
class ForumPostForm(forms.ModelForm):
    tags = TagField(
        required=False,
        help_text="Comma-separated tags (e.g., Python, Django)",
        widget=TagWidget(attrs={
            'placeholder': 'Enter tags, separated by commas'
        })
    )
    anonymous = forms.BooleanField(
        required=False,
        label="Post anonymously",
        widget=forms.CheckboxInput(attrs={'class': 'check-radio-single'})
    )
    
    class Meta:
        model = ForumPost
        fields = ['title', 'category', 'content', 'image', 'tags', 'anonymous']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Enter Title'
            }),
            'content': forms.Textarea(attrs={
                'placeholder': 'Enter your content here...'
            }),
            'image': forms.FileInput(attrs={}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(
            category_type__in=['FORUM', 'BOTH']
        )
        self.fields['category'].empty_label = "Select a category"
    

class StudentNoteForm(forms.ModelForm):
    tags = TagField(
        required=False,
        help_text="Comma-separated tags (e.g., Python, Django)",
        widget=TagWidget(attrs={
            'placeholder': 'Enter tags, separated by commas'
        })
    )
    class Meta:
        model = StudentNote
        fields = ['title', 'category', 'file', 'content', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Enter Title'
            }),
            'content': forms.Textarea(attrs={
                'placeholder': 'Enter your content here...'
            }),
            'file': forms.FileInput(attrs={
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(
            category_type__in=['NOTE', 'BOTH']
        )
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file and file.size > 5 * 1024 * 1024:  # 5MB limit
            raise forms.ValidationError("File size exceeds 5MB limit")
        return file

# --------------------------
# Interaction Forms
# --------------------------

class CommentForm(forms.ModelForm):
    anonymous = forms.BooleanField(
        required=False,
        label="Post anonymously",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    class Meta:
        model = Comment
        fields = ['content', 'anonymous']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Write your comment...'
            }),
        }

# --------------------------
# Report Forms
# --------------------------

class ReportForm(forms.ModelForm):
    object_id = forms.IntegerField(widget=forms.HiddenInput())
    class Meta:
        model = Report
        fields = ['reason']
        widgets = {
            'reason': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Describe the reason for reporting...'
            }),
        }

class AdminReportResolutionForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['status', 'admin_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'admin_notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Add resolution notes...'
            }),
        }

# --------------------------
# Textbook Management Forms
# --------------------------

class TextbookRequestForm(forms.Form):
    title = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter Textbook Title'
        })
    )
    isbn = forms.CharField(
        max_length=13,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter ISBN (10 or 13 digits)'
        })
    )
    location = forms.ModelChoiceField(
        queryset=DropLocation.objects.all().order_by('name'),
        widget=forms.Select(),
        empty_label="Choose Location",
        required=True,  # Now optional
        label="Choose Location"
    )
    
    def clean_isbn(self):
        isbn = self.cleaned_data.get('isbn')
        if not isbn.isdigit() or len(isbn) not in [10, 13]:
            raise forms.ValidationError("Invalid ISBN. It must be 10 or 13 digits.")
        return isbn
    
class TextbookDropForm(forms.ModelForm):
    drop_location = forms.ModelChoiceField(
        empty_label="Choose Drop Location",
        queryset=DropLocation.objects.all().order_by('name'),
        widget=forms.Select(),
        required=False,  # Now optional
        label="Choose Drop Location (optional)"
    )
    
    class Meta:
        model = TextbookDrop
        fields = ['textbook_title', 'textbook_isbn', 'drop_date', 'remarks', 'drop_location']
        widgets = {
            'textbook_title': forms.TextInput(attrs={
                'placeholder': 'Enter textbook title'
            }),
            'textbook_isbn': forms.TextInput(attrs={
                'placeholder': 'Enter ISBN (10 or 13 digits)'
            }),
            'drop_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local'
            }),
            'remarks': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Any remarks (optional)'
            }),
        }
    
    def clean_textbook_isbn(self):
        isbn = self.cleaned_data.get('textbook_isbn')
        if not isbn.isdigit() or len(isbn) not in [10, 13]:
            raise forms.ValidationError("ISBN must be 10 or 13 digits.")
        return isbn
    

class DropLocationForm(forms.ModelForm):
    class Meta:
        model = DropLocation
        fields = ['name', 'address', 'lat', 'lng']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'lat': forms.HiddenInput(),
            'lng': forms.HiddenInput(),
        }

class TextbookSearchForm(forms.Form):
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search textbooks...'
        })
    )

class TextbookManagementForm(forms.ModelForm):
    class Meta:
        model = Textbook
        fields = ['title', 'isbn', 'stock', 'locations', 'relevant_categories']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'locations': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'relevant_categories': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }
    
    def clean_isbn(self):
        isbn = self.cleaned_data['isbn']
        if not (len(isbn) in [10, 13] and isbn.isdigit()):
            raise forms.ValidationError("Invalid ISBN format (must be 10 or 13 digits)")
        return isbn

# --------------------------
# Donation & Notification Forms
# --------------------------

class  DonationForm(forms.ModelForm):
    amount = forms.DecimalField(
        min_value=5.00,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={ 'step': '5.00'})
    )
    class Meta:
        model = Donation
        fields = ['amount', 'receipt_email', 'first_name', 'last_name']
        widgets = {
            'receipt_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class NotificationSettingsForm(forms.ModelForm):
    NOTIFICATION_CHOICES = [
        ('reply', 'New Replies'),
        ('request', 'Textbook Updates'),
        ('level', 'Level Up Notifications'),
    ]
    notification_preferences = forms.MultipleChoiceField(
        choices=NOTIFICATION_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    class Meta:
        model = User
        fields = ['notification_preferences']

# --------------------------
# Category Management Form
# --------------------------

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'category_type']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'category_type': forms.Select(attrs={'class': 'form-select'}),
        }

# --------------------------
# Additional Features Forms
# --------------------------

class MutePostForm(forms.Form):
    mute_duration = forms.ChoiceField(
        choices=[(7, '1 Week'), (30, '1 Month'), (365, '1 Year')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class ActivityFilterForm(forms.Form):
    ACTIVITY_TYPES = [
        ('all', 'All Activities'),
        ('post', 'Forum Posts'),
        ('note', 'Note Uploads'),
        ('textbook', 'Textbook Requests'),
        ('donation', 'Donations'),
    ]
    activity_type = forms.ChoiceField(
        choices=ACTIVITY_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class RequestHistoryFilterForm(forms.Form):
    STATUS_CHOICES = [
        ('all', 'All Statuses'),
        ('P', 'Pending'),
        ('A', 'Approved'),
        ('D', 'Denied'),
        ('C', 'Completed'),
    ]
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )