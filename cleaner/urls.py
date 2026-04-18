from django.urls import path
from . import views

urlpatterns = [
    # 🔹 Home page
    path('', views.home, name='home'),

    # 🔹 Upload file
    path('upload/', views.upload_file, name='upload'),

    # 🔹 Preview page (file info + graph)
    path('preview/', views.preview, name='preview'),

    # 🔹 Clean Now button → ML cleaning
    path('clean/', views.clean_data, name='clean'),

    # 🔹 Output page (result + accuracy)
    path('output/', views.output, name='output'),

    # 🔹 Download cleaned file
    path('download/', views.download, name='download'),

    path('history/', views.history, name='history'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('resend_otp/', views.resend_otp, name='resend_otp'),
]