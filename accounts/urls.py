from django.urls import path
from .import views


urlpatterns=[
  path('register/',views.register,name='register'),
  path('login/',views.login,name='login'),
  path('logout/',views.logout,name='logout'),
  path('home1', views.home1, name='home1'),
  path('register/otp/<str:uid>/', views.otpVerify, name='otp'),
  path('resend_otp',views.resend_otp,name="resend_otp"),
  path('login/otp_login/<str:uid>/', views.otpVerify_login, name='otp_login'),
  path('resend_otp_login',views.resend_otp_login,name="resend_otp_login"),
  path('dashboard/',views.dashboard,name='dashboard'),

]


