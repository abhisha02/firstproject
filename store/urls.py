
from django.urls import path
from .import views

urlpatterns = [
  
    path('',views.store,name='store'),
    path('category/<slug:category_slug>/',views.store,name='products_by_category'),
    path('category/<slug:category_slug>/<slug:product_slug>/',views.product_detail,name='product_detail'),
    path('search/',views.search,name='search'),
    path('filter-products/',views. filter_products,name=' filter_products'),
    path('color-filter/',views.color_filter,name='color_filter'),
    
   

] 