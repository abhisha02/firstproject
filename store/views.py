from django.shortcuts import render,get_object_or_404
from .models import Product
from category.models import Category
from django.core.exceptions import ObjectDoesNotExist
from carts.views import _cart_id
from carts.models import CartItem
from django.core.paginator import EmptyPage,PageNotAnInteger,Paginator
from django.http import HttpResponse
from django.db.models import Q
from django.db.models import Count





# Create your views here.
def store(request,category_slug=None):
 

  categories=None
  products=None

  if category_slug!=None:
    categories=get_object_or_404(Category,slug=category_slug)
    products=Product.objects.filter(category=categories,is_available=True).order_by('id')
    paginator=Paginator(products,3)
    page=request.GET.get('page')
    paged_products=paginator.get_page(page)
    product_count=products.count()
  else:
   products=Product.objects.all().filter(is_available=True)
   paginator=Paginator(products,3)
   page=request.GET.get('page')
   paged_products=paginator.get_page(page)
   product_count=products.count()
  context={
        'products': paged_products,
        'product_count':product_count,
    }
  return render(request,'store/store.html',context)

def product_detail(request,category_slug,product_slug):
  try:
    single_product=Product.objects.get(category__slug=category_slug,slug=product_slug)
    additional_images = single_product.productimage_set.all()
    in_cart=CartItem.objects.filter(cart__cart_id=_cart_id(request),product=single_product).exists()
   
  except Exception as e:     
     raise e
  
  context={
    'single_product':single_product,
    'in_cart':in_cart,
    'additional_images':additional_images,
  }
  return render(request,'store/product_detail.html',context)

def search(request):
  if 'keyword' in request.GET:
    keyword=request.GET['keyword']
    if keyword:
     products=Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword) |Q(product_name__icontains=keyword))

     product_count=products.count()
    context={
      'products':products,
      'product_count':product_count,
    }

  return render(request,'store/store.html',context)

def filter_products(request):
    
    if request.method == 'GET':
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')

        # Assuming 'price' is the field in your Product model representing the price

        if min_price and max_price:
            products = Product.objects.filter(price__gte=min_price, price__lte=max_price)
            product_count=products.count()
        elif min_price:
            products = Product.objects.filter(price__gte=min_price)
            product_count=products.count()
        elif max_price:
            products = Product.objects.filter(price__lte=max_price)
            product_count=products.count()
        else:
            products = Product.objects.all()
            product_count=products.count()
        context={
        'products': products,
        'product_count':product_count,
        'min_price': min_price,
        'max_price':max_price
                 }

        return render(request,'store/store.html',context)

    return render(request, 'store/store.html')  # Render the template if the request method is not GET

def color_filter(request):
    if request.method == 'GET':
        selected_colors = request.GET.getlist('color')

        products = Product.objects.all()

        if selected_colors:
            # Filter products based on color variations
            products = products.filter(variation__variation_category='color', variation__variation_value__in=selected_colors)

            # Group products by ID and count the number of unique color variations
            products = products.annotate(color_count=Count('variation__variation_value')).filter(color_count=len(selected_colors))

        product_count = products.count()

        context = {
            'products': products,
            'product_count': product_count,
        }

        return render(request, 'store/store.html', context)

    return render(request, 'store/store.html')