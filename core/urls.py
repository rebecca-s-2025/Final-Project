from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Core Pages
    path('', views.home, name='home'),
    
    # Authentication & Password Reset
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    
    path('password-reset/', auth_views.PasswordResetView.as_view(
         template_name='profile/password_reset.html',
         email_template_name='profile/password_reset_email.txt',
         html_email_template_name='profile/password_reset_email.html',
         subject_template_name='profile/password_reset_subject.txt',
         extra_email_context={'custom_subject': 'Reset Your Password on EducAid'},
         ), name='password_reset'),
    
     path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='profile/password_reset_done.html'), 
          name='password_reset_done'),
     
     path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='profile/password_reset_confirm.html'), 
          name='password_reset_confirm'),

     path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='profile/password_reset_complete.html'), 
          name='password_reset_complete'),
    
    # Category Management (used by both forum and notes)
    path('categories/', views.forum_category_list, name='category_list'),
    
    # Forum System
     path('forums/', views.forum_category_list, name='forum_category_list'),
     path('forums/category/<int:category_id>/', views.forum_post_list, name='forum_post_list'),
     path('forums/category/<int:category_id>/create/', views.forum_post_create, name='forum_post_create'),
     path('forums/post/<int:post_id>/', views.forum_post_detail, name='forum_post_detail'),
     path('forums/post/<int:post_id>/like/', views.like_post, name='like_post'),
     path('forums/comment/<int:comment_id>/like/', views.like_comment, name='like_comment'),
     
    # Student Notes System
     path('notes/', views.notes_category_list, name='notes_category_list'),
     path('notes/category/<int:category_id>/', views.notes_list, name='notes_list'),
     path('notes/category/<int:category_id>/create/', views.note_create, name='note_create'),
     path('note/<int:note_id>/', views.note_detail, name='note_detail'),
     path('note/<int:note_id>/like/', views.like_note, name='like_note'),
     path('note/comment/<int:comment_id>/like/', views.like_comment_note, name='like_comment_note'),
    
    # Textbook Management
    path('textbook-requests/', views.browse_textbooks_requests, name='list_textbooks_requests'),
    path('textbook-requests/create/', views.textbook_request, name='create_textbook_request'),
    path('textbook-request/fullfill/<int:textbook_request_id>', views.fullfill_textbook_request, name='fullfill_textbook_request'),
#     path('textbook-requests/manage/', views.textbook_manage, name='textbook_manage'),
    
    # Reporting System
    path('report/<str:content_type>/<int:object_id>/', views.report_create, name='report_create'),
    path('reports/', views.report_list, name='report_list'),
    path('reports/<int:report_id>/resolve/', views.report_resolve, name='report_resolve'),
    
    # User Profiles
    path('profile/', views.view_profile, name='view_profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/change-password/', 
         auth_views.PasswordChangeView.as_view(template_name='profile/password_change.html'), 
         name='password_change'),
    path('profile/change-password/done/', 
     auth_views.PasswordChangeDoneView.as_view(template_name='profile/password_change_done.html'), 
     name='password_change_done'),
    path('profile/<str:username>/', views.public_profile, name='public_profile'),
    
    # Donations
    path('donate/', views.donate, name='donate'),
    
    # Notification
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    
    
    # Textbook Drop
    path('dropped-textbooks/', views.list_dropped_textbooks, name='list_dropped_textbooks'),
    path('drop-textbook/', views.drop_textbook, name='drop_textbook'),
    # For editing an existing drop location
    path('drop-textbook-form/<int:location_id>/', views.drop_textbook_form, name='drop_textbook_form_update'),
    
    #contact us
    path('contact-submit/', views.contact_form_submit, name='contact_submit'),
    
    # Error Handling (optional: actual error handlers are set via handler404/500)
    path('404/', views.handle_404, {'exception': Exception()}),
    path('500/', views.handle_500),
]

handler404 = 'core.views.handle_404'
handler500 = 'core.views.handle_500'