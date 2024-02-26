from django.shortcuts import render,redirect,get_object_or_404
from store.models import Product
from carts.models import Cart,CartItem
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from store.models import Variation
from django.contrib.auth.decorators import login_required
from accounts.models import Address
from orders.models import Order
from django.http import JsonResponse
from django.contrib import messages
from store.models import WishList
from django.db.models import Count





def _cart_id(request):
  cart=request.session.session_key
  if not cart:
    cart=request.session.create()
  return cart

def add_cart(request,product_id):
  current_user=request.user
  product=Product.objects.get(id=product_id)

  try:
   wishlist_item = get_object_or_404(WishList, user=current_user, product__product_name=product.product_name)
   wishlist_item.product.remove(product)
   wishlist_item.save()
  except:
   pass 
  if current_user.is_authenticated:
        product_variation=[]
        if request.method=='POST':
          for item in request.POST:
            key=item
            value=request.POST[key]
            try:
              variation=Variation.objects.get(product=product,variation_category__iexact=key,variation_value__iexact=value)
              product_variation.append(variation)
            except:
              pass
        is_cart_item_exists=CartItem.objects.filter(product=product,user=current_user).exists()
        if is_cart_item_exists:
          cart_item=CartItem.objects.filter(product=product,user=current_user)
          #check if current in exisring
          ex_var_list=[]
          id=[]
          for item in cart_item:
            existing_variation=item.variations.all()
            ex_var_list.append(list(existing_variation))
            id.append(item.id)
          if product_variation in ex_var_list:
            #increase cart_item quantity
            index=ex_var_list.index(product_variation)
            item_id=id[index]
            item=CartItem.objects.get(product=product,id=item_id)
            item.quantity+=1
            item.save()
          else:
            #create new cart item
           item=CartItem.objects.create(product=product,quantity=1,user=current_user)
           if len(product_variation) >0:
             item.variations.clear()
             item.variations.add(*product_variation)
          #cart_item.quantity+=1
             item.save()
        else:
          cart_item=CartItem.objects.create(
            product=product,
            quantity=1,
            user=current_user,
          )
          if len(product_variation) >0:
            cart_item.variations.clear()
            cart_item.variations.add(*product_variation)
          cart_item.save()
        return redirect('cart')
   #if the user is not authenticated    
  else:
      product_variation=[]
      if request.method=='POST':
        for item in request.POST:
          key=item
          value=request.POST[key]
          try:
            variation=Variation.objects.get(product=product,variation_category__iexact=key,variation_value__iexact=value)
            product_variation.append(variation)
          except:
            pass
      try:
        cart=Cart.objects.get(cart_id=_cart_id(request))
      except Cart.DoesNotExist:
        cart=Cart.objects.create(
          cart_id=_cart_id(request)
        )
      cart.save()
      is_cart_item_exists=CartItem.objects.filter(product=product,cart=cart).exists()
      if is_cart_item_exists:
        cart_item=CartItem.objects.filter(product=product,cart=cart)
        #check if current in exisring
        ex_var_list=[]
        id=[]
        for item in cart_item:
          existing_variation=item.variations.all()
          ex_var_list.append(list(existing_variation))
          id.append(item.id)
        print(ex_var_list)  
        if product_variation in ex_var_list:
          #increase cart_item quantity
          index=ex_var_list.index(product_variation)
          item_id=id[index]
          item=CartItem.objects.get(product=product,id=item_id)
          item.quantity+=1
          item.save()
        else:
          #create new cart item
         item=CartItem.objects.create(product=product,quantity=1,cart=cart)
         if len(product_variation) >0:
          item.variations.clear()
          item.variations.add(*product_variation)
        #cart_item.quantity+=1
          item.save()
      else:
        cart_item=CartItem.objects.create(
          product=product,
          quantity=1,
          cart=cart,
        )
        if len(product_variation) >0:
          cart_item.variations.clear()
          cart_item.variations.add(*product_variation)
        cart_item.save()
      return redirect('cart')

def remove_cart(request,product_id,cart_item_id):
  product=get_object_or_404(Product,id=product_id)
  try:
   if request.user.is_authenticated:
     cart_item=CartItem.objects.get(product=product,user=request.user,id=cart_item_id)
   else:
     cart=Cart.objects.get(cart_id=_cart_id(request))
     cart_item=CartItem.objects.get(product=product,cart=cart,id=cart_item_id)
   if cart_item.quantity>1:
     cart_item.quantity-=1
     cart_item.save()
   else:
     cart_item.delete()
  except:
    pass
  return redirect('cart')  

def remove_cart_item(request,product_id,cart_item_id):
  product=get_object_or_404(Product,id=product_id)
  if request.user.is_authenticated:
    cart_item=CartItem.objects.get(product=product,user=request.user,id=cart_item_id)
  else:
    cart=Cart.objects.get(cart_id=_cart_id(request))
    cart_item=CartItem.objects.get(product=product,cart=cart,id=cart_item_id)
  cart_item.delete()
  return redirect('cart')

def cart(request,total=0,quantity=0,cart_items=None):
  try:
    tax=0
    grand_total=0
    if request.user.is_authenticated:
      cart_items=CartItem.objects.filter(user=request.user,is_active=True)
    else:
      cart=Cart.objects.get(cart_id=_cart_id(request))
      cart_items=CartItem.objects.filter(cart=cart,is_active=True)
   
    total_discount=0
    for cart_item in cart_items:
      if cart_item.product.offer_percentage > 0:
       total+=(cart_item.product.offer_price*cart_item.quantity)
       total_discount+=(cart_item.product.price*cart_item.quantity)-(cart_item.product.offer_price*cart_item.quantity)
      else:
       total+=(cart_item.product.price*cart_item.quantity)
      quantity+=cart_item.quantity
    tax=(2 *total/100)
    delivery_charge=100
    grand_total=total+tax+delivery_charge
    if total_discount:
      total_discount+=(2 *total_discount/100)
  
    
  except ObjectDoesNotExist:
    pass
  
  context={
    'total':total,
    'quantity':quantity,
    'cart_items':cart_items,
    'tax':tax,
    'grand_total':grand_total,
    'delivery_charge':delivery_charge,
    'total_discount':total_discount
  }
  return render(request,'store/cart.html',context)


@login_required(login_url='login')
def checkout(request,total=0,quantity=0,cart_items=None):
  try:
    tax=0
    grand_total=0
    if request.user.is_authenticated:
      cart_items=CartItem.objects.filter(user=request.user,is_active=True)
    else:
      cart=Cart.objects.get(cart_id=_cart_id(request))
      cart_items=CartItem.objects.filter(cart=cart,is_active=True)
    total1=0
    total_discount=0
    for cart_item in cart_items:
      if cart_item.product.stock<cart_item.quantity:
        cart_item.quantity=cart_item.product.stock
        messages.success(request, f'Only {cart_item.product.stock} items available for {cart_item.product.product_name} .')
        return redirect("cart")
      if cart_item.product.offer_percentage > 0:
       total+=(cart_item.product.offer_price*cart_item.quantity)
       total_discount+=(cart_item.product.price*cart_item.quantity)-(cart_item.product.offer_price*cart_item.quantity)
      else:
       total+=(cart_item.product.price*cart_item.quantity)
      quantity+=cart_item.quantity
    tax=(2 *total/100)
    delivery_charge=100
    grand_total=total+tax+delivery_charge
    if total_discount:
      total_discount+=(2 *total_discount/100)
  except ObjectDoesNotExist:
    pass
  current_user = request.user
  user_addresses = Address.objects.filter(user=current_user,on_del=True)
  if request.method == 'POST':
        # User selected an existing address
        selected_address_id = request.POST.get('selected_address', None)
        if selected_address_id:
            address = Address.objects.get(id=selected_address_id)
        else:
            pass
        data = Order()
        data.user = current_user
        data.address = address
  for item in cart_items:
        if item.product.offer_percentage:
         item.total_price = item.quantity * item.product.offer_price
        else:
           item.total_price = item.quantity * item.product.price

  context={
    'total':total,
    'quantity':quantity,
    'cart_items':cart_items,
    'tax':tax,
    'grand_total':grand_total,
    'user_addresses' : user_addresses,
    'total_discount':total_discount
  }
  return render(request,'store/checkout.html',context)

def update(request):  
    if request.method == 'POST':   
        try:
            
            prod_id = int(request.POST.get('product_id'))
            prod_qty = int(request.POST.get('product_qty'))
            cartitem_id=int(request.POST.get('cartitem_id'))
            product=get_object_or_404(Product,id=prod_id)
            if request.user.is_authenticated:
              cart_item=CartItem.objects.get(product=product,user=request.user,id=cartitem_id)
            else:
              cart=Cart.objects.get(cart_id=_cart_id(request))
              cart_item=CartItem.objects.get(product=product,cart=cart,id=cartitem_id)
            if cart_item.quantity <prod_qty:
             cart_item.quantity = prod_qty+1
            else:
              cart_item.quantity = prod_qty-1

            cart_item.save()
            total=(cart_item.product.price*cart_item.quantity)
            request.session['total'] = total
            tax=(2 *total/100)
            grand_total=total+tax
            cartitem_quantity=cart_item.quantity
            return JsonResponse({'total':total})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)
  