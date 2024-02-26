from django.urls import path
from .import views


urlpatterns=[
  #Registration
  path('register/',views.register,name='register'),
  path('login/',views.login,name='login'),
  path('logout/',views.logout,name='logout'),
  path('home1', views.home1, name='home1'),
  path('otpVerify/', views.otpVerify, name='otpVerify'),
  path('resend-otp',views.resend_otp,name="resend_otp"),

  #login
  path('otpVerify-login/', views.otpVerify_login, name='otpVerify_login'),
  path('resend-otp-login',views.resend_otp_login,name="resend_otp_login"),
  path('dashboard/',views.dashboard,name='dashboard'),
  path('login-admin',views.login_admin,name="login_admin"),
  path('dashboard-admin',views.dashboard_admin,name="dashboard_admin"),
  path('logout-admin',views.logout_admin,name="logout_admin"),
  
  #admin user management
  path('users-list',views.users_list,name="users_list"),
  path('toggle-user-status/<int:user_id>/',views.toggle_user_status,name="toggle_user_status"),

  #admin category management
  path('category-list/',views.category_list,name="category_list"),
  path('category-add',views.category_add,name="category_add"),
  path('category-update/<int:category_id>', views.category_update, name="category_update"),
  path('category-delete/<int:id>/', views.category_delete, name="category_delete"),

  #admin product management
  path('product-list', views.product_list, name="product_list"),
  path('product-add', views.product_add, name="product_add"),
  path('product-update/<int:product_id>', views.product_update, name="product_update"),
  path('product-delete/<slug:id>', views.product_delete, name="product_delete"),

  #admin variant management
  path('variant-list', views.variant_list, name="variant_list"),
  path('variant-add', views.variant_add, name='variant_add'),
  path('variant-update/<int:variant_id>', views.variant_update, name="variant_update"),
  path('variant-delete/<int:variant_id>', views.variant_delete, name="variant_delete"),
  
  #profile and order management
  path('my-orders/',views.my_orders,name="my_orders"),
  path('edit_profile/',views.edit_profile,name="edit_profile"),
  path('add_profile/',views.add_profile,name="add_profile"),
  path('change-password/',views.change_password,name="change_password"),
  path('order-detail/<int:order_id>/',views.order_detail,name="order_detail"),
  path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
  path('address-list/', views.address_list, name='address_list'),
  path('order-list-admin', views.order_list_admin, name="order_list_admin"),
  path('change-order-status/<int:order_id>/', views.change_order_status, name='change_order_status'),
  path('cancel-order2/<int:order_id>/', views.cancel_order2, name='cancel_order2'),
  path('return-order/<int:order_id>/', views.return_order, name='return_order'),
  path('forgot-password/',views.forgot_password,name="forgot_password"),
  path('admin-coupon-list/',views.admin_coupon_list,name="admin_coupon_list"),

  #Coupon
  path('coupon-add/',views.coupon_add,name="coupon_add"),
  path('coupon-edit/<int:coupon_id>', views.coupon_edit, name="coupon_edit"),
  path('coupon-delete/<int:coupon_id>', views.coupon_delete, name="coupon_delete"),

  #product offer
  path('admin-product-offer-list/',views.admin_product_offer_list,name="admin_product_offer_list"),
  path('add_product_offer/',views.add_product_offer,name="add_product_offer"),
  path('add-offer-percentage/<int:product_id>', views.add_offer_percentage, name="add_offer_percentage"),
  path('offer-edit/<int:product_id>', views.offer_edit, name="offer_edit"),
  path('offer-delete/<int:product_id>', views.offer_delete, name="offer_delete"),
  
  #wishlist
  path('wishlist/', views.wishlist, name='wishlist'),
  path('add_to_wishlist/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
  path('delete_wishlist_item/<int:wishlist_id>/<int:product_id>/', views.delete_wishlist_item, name='delete_wishlist_item')
  
  
  

]


