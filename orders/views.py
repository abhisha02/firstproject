from django.shortcuts import render
from django.http import HttpResponse
from carts.models import CartItem,Coupons,UserCoupons
from django.shortcuts import redirect
from .forms import AddressForm
from accounts.models import Address
from django.contrib import messages
from django.shortcuts import get_object_or_404
from .models import Order,OrderAddress
import datetime 
from .models import OrderProduct,Payment
from store.models import Product
import uuid
from paypal.standard.forms import PayPalPaymentsForm
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from datetime import date
from django.http import FileResponse
import io
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from io import BytesIO
import calendar
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe





def place_order(request, quantity=0, total=0):
    wallet_flag=True
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')
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
    if request.method == 'POST':
        order_address_id = request.POST.get('selected_address', None)
        data = Order()
        data.user = current_user
        data.order_total = grand_total
        data.tax = tax
        data.ip = request.META.get('REMOTE_ADDR')
        data.save()
        if order_address_id:
            # Retrieve the address associated with the order
            order_address = Address.objects.get(id=order_address_id)
            orderad=OrderAddress()
            orderad.order=data
            orderad.phone_number=order_address.phone_number
            orderad.address_line_1=order_address.address_line_1
            orderad.address_line_2=order_address.address_line_2
            orderad.city=order_address.city
            orderad.state=order_address.state
            orderad.country=order_address.country
            orderad.zipcode=order_address.zipcode
            orderad.save()

            data.address = order_address
            data.save()
        # #Generate Order Number:
        yr = int(date.today().strftime('%Y'))
        mt = int(date.today().strftime('%m'))
        dt = int(date.today().strftime('%d'))
        d = date(yr,mt,dt)
        current_date = d.strftime("%Y%m%d")
        order_number = current_date + str(data.id)
        data.order_number = order_number
        data.save()
        order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
        order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
        request.session['order_address_id']=order_address.id
        request.session['total']=total
        request.session['total_discount']=total_discount
        request.session['grand_total']=grand_total
        request.session['tax']=tax
        request.session['wallet_flag']=wallet_flag
        request.session['order_id']=order.id

        for item in cart_items:
            if item.product.offer_percentage:
             item.total_price = item.quantity * item.product.offer_price
            else:
             item.total_price = item.quantity * item.product.price
        context = {
            'order_address' : order_address,
            'order': order,
            'cart_items': cart_items,
            'total': total,
            'tax': tax,
            'grand_total': grand_total,
            'delivery_charge':delivery_charge,
            'total_discount':total_discount,
            'wallet_flag':wallet_flag

        }
        
        return render(request, 'store/place_order.html', context)
    else:
        return HttpResponse('Error!')
    

def make_payments(request, order_id):
    current_user = request.user
    # Retrieve the order using the given order_id and user
    order = get_object_or_404(Order, id=order_id, user=current_user, is_ordered=False)
    if request.method == 'POST':
        if order and (order.status == 'Pending' or order.status == 'Payment Pending'):
            payment_method = request.POST.get('paymentMethod')
            # Perform different actions based on the selected payment method
            if payment_method == 'CashOnDelivery':
                if order.order_total>1000:
                    order_address_id = request.session.get('order_address_id')
                    total = request.session.get('total')
                    grand_total = request.session.get('grand_total')
                    tax=request.session.get('tax')
                    wallet_flag=request.session.get('wallet_flag')
                    total_discount=request.session.get('total_discount')
                    order_address=Address.objects.get(user=current_user,id=order_address_id)
                    cart_items = CartItem.objects.filter(user=request.user)
                    delivery_charge=100
                    try:
                     coupon_discount=request.session.get('coupon_discount')
                    except:
                        pass
                    for item in cart_items:
                        if item.product.offer_percentage:
                         item.total_price = item.quantity * item.product.offer_price
                        else:
                         item.total_price = item.quantity * item.product.price
                    context = {
                        'coupon_discount':coupon_discount,
                        'order_address' : order_address,
                        'order': order,
                        'cart_items': cart_items,
                        'total': total,
                        'tax': tax,
                        'grand_total': grand_total,
                        'delivery_charge':delivery_charge,
                        'total_discount':total_discount,
                        'wallet_flag':wallet_flag
                    }
                    messages.error(request, 'Orders above Rs 1000 cant be placed using COD.Try another payment method')
                    return render(request, 'store/place_order.html', context)
                # If payment method is Cash On Delivery, update the order status
                order.status = 'Order Confirmed'
                order.is_ordered = True
                order.save()
                # Create a new Payment instance with a unique payment_id
                payment_id = uuid.uuid4().hex
                payment = Payment.objects.create(
                    user = current_user,
                    payment_id = payment_id,
                    amount_paid = order.order_total,
                    status = 'Delivered'
                )
                order.payment = payment
                order.save()
                # Move cart item to OrderProduct Table:
                cart_items = CartItem.objects.filter(user=request.user)
                for item in cart_items:
                    orderproduct = OrderProduct()
                    orderproduct.order_id = order.id
                    orderproduct.payment = payment
                    orderproduct.user_id = request.user.id
                    orderproduct.product_id = item.product_id
                    orderproduct.quantity = item.quantity
                    orderproduct.product_price = item.product.price
                    orderproduct.ordered = True
                    orderproduct.save()
                    cart_item = CartItem.objects.get(id=item.id)
                    product_variant = cart_item.variations.all()
                    orderproduct = OrderProduct.objects.get(id=orderproduct.id)
                    orderproduct.variant.set(product_variant)
                    orderproduct.save()
                    #Reduce the stock of product sold:
                    product = Product.objects.get(id=item.product_id)
                    product.stock -= item.quantity
                    product.save()
                #Clear Cart:
                CartItem.objects.filter(user=request.user).delete()
                messages.success(request, 'Order placed successfully.')
                return redirect('order_confirmation', order_id=order.id)
            elif payment_method == 'wallet':
                # If payment method is Cash On Delivery, update the order status
                

                user=request.user
                if user.wallet>=order.order_total:
                    user.wallet-=order.order_total
                    user.save()
                    order.status = 'Order Confirmed'
                    order.is_ordered = True
                    order.save()
                    # Create a new Payment instance with a unique payment_id
                    payment_id = uuid.uuid4().hex
                    payment = Payment.objects.create(
                        user = current_user,
                        payment_id = payment_id,
                        amount_paid = order.order_total,
                        status = 'Delivered'
                    )
                    order.payment = payment
                    order.save()
                    # Move cart item to OrderProduct Table:
                    cart_items = CartItem.objects.filter(user=request.user)
                    for item in cart_items:
                        orderproduct = OrderProduct()
                        orderproduct.order_id = order.id
                        orderproduct.payment = payment
                        orderproduct.user_id = request.user.id
                        orderproduct.product_id = item.product_id
                        orderproduct.quantity = item.quantity
                        orderproduct.product_price = item.product.price
                        orderproduct.ordered = True
                        orderproduct.save()
                        cart_item = CartItem.objects.get(id=item.id)
                        product_variant = cart_item.variations.all()
                        orderproduct = OrderProduct.objects.get(id=orderproduct.id)
                        orderproduct.variant.set(product_variant)
                        orderproduct.save()
                        #Reduce the stock of product sold:
                        product = Product.objects.get(id=item.product_id)
                        product.stock -= item.quantity
                        product.save()
                    #Clear Cart:
                    CartItem.objects.filter(user=request.user).delete()
                    messages.success(request, 'Order placed successfully.')
                    return redirect('order_confirmation', order_id=order.id)
                else:
                    messages.error(request, 'Wallet balance insufficient')
                    return redirect('checkout')
            elif payment_method == 'PayPal':
            
       
                host = request.get_host()
                paypal_checkout = {
                    'business': settings.PAYPAL_RECEIVER_EMAIL,
                    'amount': order.order_total,
                    'invoice': uuid.uuid4(),
                    'currency_code': 'USD',
                    'notify_url': f"http://{host}{reverse('paypal-ipn')}",
                    'return_url': f"http://{host}{reverse('paypal_payment_success', kwargs={'order_id': order.id})}",
                    'cancel_url': f"http://{host}{reverse('paypal_payment_failed', kwargs={'order_id': order.id})}",
                }
                paypal_payment = PayPalPaymentsForm(initial=paypal_checkout)
                context = {
                    'order': order,
                    'paypal': paypal_payment
                }
                return render(request, 'paypal/paypal_checkout.html', context)
           
                 
            else:
                # Handle other payment methods or show an error message
                messages.error(request, 'Select a valid payment method.')
        else:
            # Handle the case where the order does not exist or is not in a suitable state for payment
            messages.error(request, 'Invalid order or order not in a valid state for payment.')
            return redirect('home')
    return render(request, 'store/place_order.html', {'order': order})

def paypal_payment_success(request, order_id):
    
    # order = get_object_or_404(Order, id=order_id)
  
    current_user = request.user
    # Retrieve the order using the given order_id and user
    order = get_object_or_404(Order, id=order_id, user=current_user, is_ordered=False)
    # update the order status
    order.status = 'Order Confirmed'
    order.is_ordered = True
    order.save()
    # Create a new Payment instance with a unique payment_id
    payment_id = uuid.uuid4().hex
    payment = Payment.objects.create(
        user=current_user,
        payment_id=payment_id,
        amount_paid=order.order_total,
        status='Completed'
    )
    order.payment = payment
    order.save()
    # Move cart item to OrderProduct Table:
    cart_items = CartItem.objects.filter(user=request.user)
    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True
        orderproduct.save()
        cart_item = CartItem.objects.get(id=item.id)
        product_variant = cart_item.variations.all()
        orderproduct = OrderProduct.objects.get(id=orderproduct.id)
        orderproduct.variant.set(product_variant)
        orderproduct.save()
        # Reduce the stock of product sold:
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()
    # Clear Cart:
    CartItem.objects.filter(user=request.user).delete()
    messages.success(request, 'Order placed successfully.')
    return redirect('order_confirmation', order_id=order.id)

def paypal_payment_failed(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'paypal/paypal-payment-failed.html', {'order': order})

def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'store/order_confirmation.html', {'order': order})

def create_address(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            form.instance.user = request.user
            full_name=form.cleaned_data['full_name']
            phone_number=form.cleaned_data['phone_number']
            address_line_1=form.cleaned_data['address_line_1']
            address_line_2=form.cleaned_data['address_line_2']
            city=form.cleaned_data['city']
            state=form.cleaned_data['state']
            country=form.cleaned_data['country']
            zipcode=form.cleaned_data['zipcode']
            address=Address.objects.create(user=form.instance.user,full_name=full_name,phone_number=phone_number,address_line_1=address_line_1,address_line_2=address_line_2,city=city,state=state,country=country,zipcode=zipcode)
            address.save()
            previous_path = request.META.get('HTTP_REFERER', '/')
            messages.success(request, 'Address Added Successfully.')
            return redirect('checkout')          
    else:
        form = AddressForm() 
    return render(request, 'store/add_address.html', {'form': form})

def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    if request.method == 'POST':
        
        form = AddressForm(request.POST)
        if form.is_valid():
           
            form.instance.user = request.user
            full_name=form.cleaned_data['full_name']
            phone_number=form.cleaned_data['phone_number']
            address_line_1=form.cleaned_data['address_line_1']
            address_line_2=form.cleaned_data['address_line_2']
            city=form.cleaned_data['city']
            state=form.cleaned_data['state']
            country=form.cleaned_data['country']
            zipcode=form.cleaned_data['zipcode']
            address2=Address.objects.create(user=form.instance.user,full_name=full_name,phone_number=phone_number,address_line_1=address_line_1,address_line_2=address_line_2,city=city,state=state,country=country,zipcode=zipcode)
            address2.save()
            address.on_del=False
            address.save()
            messages.success(request, 'Address Updated Successfully')
            return redirect('checkout')     
    else:
        form = AddressForm(instance=address)
    return render(request, 'store/edit_address.html', {'form': form})

def delete_address(request, address_id):
    address_to_delete = Address.objects.get(id=address_id)
    address_to_delete.on_del=False
    address_to_delete.save()
    messages.success(request, 'Address deleted.')
    return redirect('checkout')

def create_address2(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            form.instance.user = request.user
            full_name=form.cleaned_data['full_name']
            phone_number=form.cleaned_data['phone_number']
            address_line_1=form.cleaned_data['address_line_1']
            address_line_2=form.cleaned_data['address_line_2']
            city=form.cleaned_data['city']
            state=form.cleaned_data['state']
            country=form.cleaned_data['country']
            zipcode=form.cleaned_data['zipcode']
            address=Address.objects.create(user=form.instance.user,full_name=full_name,phone_number=phone_number,address_line_1=address_line_1,address_line_2=address_line_2,city=city,state=state,country=country,zipcode=zipcode)
            address.save()
            previous_path = request.META.get('HTTP_REFERER', '/')
            messages.success(request, 'Address Added Successfully.')
            return redirect('address_list')         
    else:
        form = AddressForm()
    return render(request, 'store/add_address2.html', {'form': form})

def edit_address2(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            form.instance.user = request.user
            full_name=form.cleaned_data['full_name']
            phone_number=form.cleaned_data['phone_number']
            address_line_1=form.cleaned_data['address_line_1']
            address_line_2=form.cleaned_data['address_line_2']
            city=form.cleaned_data['city']
            state=form.cleaned_data['state']
            country=form.cleaned_data['country']
            zipcode=form.cleaned_data['zipcode']
            address2=Address.objects.create(user=form.instance.user,full_name=full_name,phone_number=phone_number,address_line_1=address_line_1,address_line_2=address_line_2,city=city,state=state,country=country,zipcode=zipcode)
            address2.save()
            address.on_del=False
            address.save()
            messages.success(request, 'Address Updated Successfully')
            return redirect('address_list')      
    else:
        form = AddressForm(instance=address)
    return render(request, 'store/edit_address.html', {'form': form})



def delete_address2(request, address_id):
    address_to_delete = Address.objects.filter(id=address_id)
    address_to_delete.on_del=False
    address_to_delete.save()
    messages.success(request, 'Address deleted.')
    return redirect('address_list')
    
def add_money_wallet(request):
    if request.method=="POST":
        amount = float(request.POST.get('amount', 0))
        user=request.user
        user.wallet+=amount
        user.save()
        order_address_id = request.session.get('order_address_id')
        total = request.session.get('total')
        grand_total = request.session.get('grand_total')
        tax=request.session.get('tax')
        wallet_flag=request.session.get('wallet_flag')
        total_discount=request.session.get('total_discount')
        order_id=request.session.get('order_id')
        order=Order.objects.get(id=order_id)
        order_address=Address.objects.get(user=request.user,id=order_address_id)
        cart_items = CartItem.objects.filter(user=request.user)
        delivery_charge=100
        try:
            coupon_discount=request.session.get('coupon_discount')
        except:
            pass
        for item in cart_items:
            if item.product.offer_percentage:
                item.total_price = item.quantity * item.product.offer_price
            else:
                item.total_price = item.quantity * item.product.price
        context = {
            'coupon_discount':coupon_discount,
            'order_address' : order_address,
            'order': order,
            'cart_items': cart_items,
            'total': total,
            'tax': tax,
            'grand_total': grand_total,
            'delivery_charge':delivery_charge,
            'total_discount':total_discount,
            'wallet_flag':wallet_flag,
            'wallet':user.wallet
        }
        messages.success(request, 'Money added Successfully')
        return render(request, 'store/place_order.html', context)
        
        
    return render(request,'store/add_money_wallet.html')

@login_required(login_url='login_admin')
def order_detail2(request, order_id):
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    order = Order.objects.get(order_number=order_id)
    subtotal = 0
    for i in order_detail:
        subtotal += i.product_price * i.quantity
    context = {
        'order_detail' : order_detail,
        'order' : order,
        'subtotal' : subtotal,
        'coupon_discount':order.coupon_discount
        
    }
    return render(request, 'accounts/order_detail2.html', context)

@login_required(login_url='login_admin')
def order_detail_admin(request, order_id):
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    order = Order.objects.get(order_number=order_id)
    total_product = []
    subtotal = 0
    for item in order_detail:
        product_total = item.product_price * item.quantity
        subtotal += product_total
        total_product.append({'item': item, 'total': product_total})
    context = {
        'order_detail': total_product,
        'order': order,
        'subtotal': subtotal,
    }
    return render(request, 'admin/order-detail-admin.html', context)
from datetime import datetime, timedelta

@login_required(login_url='login_admin')
def sales_report(request):
    # Calculate the start and end of the current day
    current_date = datetime.now()
    start_of_day = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1) - timedelta(microseconds=1)
    # Filter OrderProduct objects for the current day
    orders = Order.objects.filter(created_at__range=[start_of_day, end_of_day]).order_by('-created_at')
    # Calculate the sum of order amount for the current day
    total_order_amount = orders.aggregate(total_order_amount=Sum('order_total'))[
                            'total_order_amount'] or 0
    # Calculate the sum of amount_paid for the current day
    total_amount_paid = orders.aggregate(total_amount_paid=Sum('payment__amount_paid'))['total_amount_paid'] or 0
    context = {
        'current_date' : current_date,
        'orders': orders,
        'total_order_amount' : total_order_amount,
        'total_amount_paid': total_amount_paid,
    }
    return render(request, 'salesreport/daily_sales_report.html', context)

@login_required(login_url='login_admin')
def weekly_sales_report(request):
    # Calculate the start and end of the current week
    current_date = timezone.now().date()
    start_of_week = current_date - timedelta(days=current_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    # Filter Order objects for today and the past week
    start_of_day = current_date
    end_of_day = current_date + timedelta(days=1)
    start_of_last_week = start_of_week - timedelta(weeks=1)
    orders = Order.objects.filter(created_at__range=[start_of_last_week, end_of_day]).order_by('-created_at')
    # Calculate the sum of order amount for the current day
    total_order_amount = orders.aggregate(total_order_amount=Sum('order_total'))[
                             'total_order_amount'] or 0
    # Calculate the sum of amount_paid for the current day
    total_amount_paid = orders.aggregate(total_amount_paid=Sum('payment__amount_paid'))['total_amount_paid'] or 0
    context = {
        'start_of_week' : start_of_last_week,
        'end_of_week' : current_date,
        'orders': orders,
        'total_order_amount': total_order_amount,
        'total_amount_paid': total_amount_paid,
    }
    return render(request, 'salesreport/weekly_sales_report.html', context)

@login_required(login_url='login_admin')
def monthly_sales_report(request):
   # Calculate the start and end of the current day
   current_date = timezone.now().date()
  # Calculate start and end of the month
   start_of_month = current_date.replace(day=1)
   end_of_month = start_of_month.replace(month=start_of_month.month + 1) - timedelta(days=1)
  # Calculate the start of today
   start_of_today = current_date
   end_of_today = start_of_today + timedelta(days=1)
   # Calculate the start of the month one month ago
   start_of_last_month = start_of_month - timedelta(days=1)
   start_of_last_month = start_of_last_month.replace(day=1)
  # Filter Order objects for today and the past month
   orders = Order.objects.filter(created_at__range=[start_of_last_month, end_of_today]).order_by('-created_at')
    # Calculate the sum of order amount for the current month
   total_order_amount = orders.aggregate(total_order_amount=Sum('order_total'))[
                             'total_order_amount'] or 0
    # Calculate the sum of amount_paid for the current day
   total_amount_paid = orders.aggregate(total_amount_paid=Sum('payment__amount_paid'))['total_amount_paid'] or 0
   context = {
        'start_of_month' : start_of_last_month,
        'end_of_month' : current_date,
        'orders': orders,
        'total_order_amount': total_order_amount,
        'total_amount_paid': total_amount_paid,
    }
   return render(request, 'salesreport/monthly_sales_report.html', context)

@login_required(login_url='login_admin')
def yearly_sales_report(request):
    # Calculate the start and end of the current year
    current_date = datetime.now()
    start_of_year = current_date.replace(month=1, day=1)
    end_of_year = start_of_year.replace(year=start_of_year.year + 1) - timedelta(days=1)
    # Filter OrderProduct objects for the current year
    orders = Order.objects.filter(created_at__range=[start_of_year, end_of_year]).order_by('-created_at')
    # Calculate the sum of order amount for the current year
    total_order_amount = orders.aggregate(total_order_amount=Sum('order_total'))[
                             'total_order_amount'] or 0
    # Calculate the sum of amount_paid for the current day
    total_amount_paid = orders.aggregate(total_amount_paid=Sum('payment__amount_paid'))['total_amount_paid'] or 0
    context = {
        'start_of_year' : start_of_year,
        'end_of_year' : current_date,
        'orders': orders,
        'total_order_amount': total_order_amount,
        'total_amount_paid': total_amount_paid,
    }
    return render(request, 'salesreport/yearly_sales_report.html', context)

#Generate a PDF Daily Sales Report
def sales_report_pdf(request):
    buf=io.BytesIO()
    #create canvas
    c=canvas.Canvas(buf,pagesize=letter,bottomup=0)
    #create a text object
    textob=c.beginText()
    textob.setTextOrigin(inch,inch)
    textob.setFont("Helvetica",14)
    current_date = datetime.now()
    start_of_day = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1) - timedelta(microseconds=1)
    # Filter OrderProduct objects for the current day
    orders = Order.objects.filter(created_at__range=[start_of_day, end_of_day]).order_by('-created_at')
    total_order_amount = orders.aggregate(total_order_amount=Sum('order_total'))[
                            'total_order_amount'] or 0
    report=[]
    # Define column widths
    serial_width = 10
    order_number_width = 20
    full_name_width = 30
    amount_paid_width = 15
    status_width = 20
    # Define the heading
    heading = "Today's Sales"
    # Print the heading
    centered_heading = ' ' * 50+ heading
    textob.textLine( centered_heading)
    textob.textLine(" ")
    textob.textLine(" ")
# Print column titles
    column_titles = f"{'No.':<{serial_width}}{'Order Number':<{order_number_width}}{'Full Name':<{full_name_width}}{'Amount Paid':<{amount_paid_width}}  {'Status':<{status_width}}"
    textob.textLine(column_titles)
    textob.textLine(" ")

# Print order information with serial numbers
    for index, order in enumerate(orders, start=1):
    # Concatenate all attributes of the order instance into a single string
     order_info = f"{str(index):<{serial_width}}"
     order_info += f"{str(order.order_number):<{order_number_width}}"
     order_info += f"{order.address.full_name[:full_name_width-4]:<{full_name_width}}"
     order_info += f"{str(order.order_total):<{amount_paid_width}}"
     order_info += f"{order.status[:status_width]:<{status_width}}"
     textob.textLine(order_info)
    textob.textLine(" ")
    grand_total_label = "Grand Total:"
    grand_total = f"{grand_total_label:<{order_number_width}} {total_order_amount:>{order_number_width}}"
    textob.textLine(grand_total)
    c.drawText(textob)
    c.showPage()
    c.save()
    buf.seek(0)
    return FileResponse(buf,as_attachment=True,filename='dailyreport.pdf')

def weekly_report_pdf(request):
    buf=io.BytesIO()
    #create canvas
    c=canvas.Canvas(buf,pagesize=letter,bottomup=0)
    #create a text object
    textob=c.beginText()
    textob.setTextOrigin(inch,inch)
    textob.setFont("Helvetica",14)
    current_date = datetime.now()
    start_of_week = current_date - timedelta(days=current_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    # Filter OrderProduct objects for the current week
    orders = Order.objects.filter(created_at__range=[start_of_week, end_of_week]).order_by('-created_at')
    total_order_amount = orders.aggregate(total_order_amount=Sum('order_total'))[
                             'total_order_amount'] or 0
    report=[]
    # Define column widths
    serial_width = 10
    order_number_width = 20
    full_name_width = 30
    amount_paid_width = 15
    status_width = 20
    # Define the heading
    heading = "Weekly Sales Report"
    # Print the heading
    centered_heading = ' ' * 50+ heading
    textob.textLine( centered_heading)
    textob.textLine(" ")
    textob.textLine(" ")
    # Print column titles
    column_titles = f"{'No.':<{serial_width}}{'Order Number':<{order_number_width}}{'Full Name':<{full_name_width}}{'Amount Paid':<{amount_paid_width}}  {'Status':<{status_width}}"
    textob.textLine(column_titles)
    textob.textLine(" ")
    # Print order information with serial numbers
    for index, order in enumerate(orders, start=1):
    # Concatenate all attributes of the order instance into a single string
     order_info = f"{str(index):<{serial_width}}"
     order_info += f"{str(order.order_number):<{order_number_width}}"
     order_info += f"{order.address.full_name[:full_name_width-4]:<{full_name_width}}"
     order_info += f"{str(order.order_total):<{amount_paid_width}}"
     order_info += f"{order.status[:status_width]:<{status_width}}"
     textob.textLine(order_info)
    textob.textLine(" ")
    grand_total_label = "Grand Total:"
    grand_total = f"{grand_total_label:<{order_number_width}} {total_order_amount:>{order_number_width}}"
    textob.textLine(grand_total)
    c.drawText(textob)
    c.showPage()
    c.save()
    buf.seek(0)
    return FileResponse(buf,as_attachment=True,filename='weeklyreport.pdf')

def monthly_report_pdf(request):
    buf=io.BytesIO()
    #create canvas
    c=canvas.Canvas(buf,pagesize=letter,bottomup=0)
    #create a text object
    textob=c.beginText()
    textob.setTextOrigin(inch,inch)
    textob.setFont("Helvetica",14)
    # Calculate the start and end of the current day
    current_date = datetime.now()
    start_of_month = current_date.replace(month=1, day=1)
    end_of_month = start_of_month.replace(year=start_of_month.year + 1) - timedelta(days=1)
    # Filter OrderProduct objects for the current day
    orders = Order.objects.filter(created_at__range=[start_of_month, end_of_month]).order_by('-created_at')
    total_order_amount = orders.aggregate(total_order_amount=Sum('order_total'))[
                             'total_order_amount'] or 0
    report=[]
    # Define column widths
    serial_width = 10
    order_number_width = 20
    full_name_width = 30
    amount_paid_width = 15
    status_width = 20
    # Define the heading
    heading = "Monthly Sales Report"
    # Print the heading
    centered_heading = ' ' * 50+ heading
    textob.textLine( centered_heading)
    textob.textLine(" ")
    textob.textLine(" ")
    # Print column titles
    column_titles = f"{'No.':<{serial_width}}{'Order Number':<{order_number_width}}{'Full Name':<{full_name_width}}{'Amount Paid':<{amount_paid_width}}  {'Status':<{status_width}}"
    textob.textLine(column_titles)
    textob.textLine(" ")
    # Print order information with serial numbers
    for index, order in enumerate(orders, start=1):
    # Concatenate all attributes of the order instance into a single string
     order_info = f"{str(index):<{serial_width}}"
     order_info += f"{str(order.order_number):<{order_number_width}}"
     order_info += f"{order.address.full_name[:full_name_width-4]:<{full_name_width}}"
     order_info += f"{str(order.order_total):<{amount_paid_width}}"
     order_info += f"{order.status[:status_width]:<{status_width}}"
     textob.textLine(order_info)
    textob.textLine(" ")
    grand_total_label = "Grand Total:"
    grand_total = f"{grand_total_label:<{order_number_width}} {total_order_amount:>{order_number_width}}"
    textob.textLine(grand_total)
    c.drawText(textob)
    c.showPage()
    c.save()
    buf.seek(0)
    return FileResponse(buf,as_attachment=True,filename='monthlyreport.pdf')

def yearly_report_pdf(request):
    buf=io.BytesIO()
    #create canvas
    c=canvas.Canvas(buf,pagesize=letter,bottomup=0)
    #create a text object
    textob=c.beginText()
    textob.setTextOrigin(inch,inch)
    textob.setFont("Helvetica",14)
    # Calculate the start and end of the current day
    current_date = datetime.now()
    start_of_year = current_date.replace(month=1, day=1)
    end_of_year = start_of_year.replace(year=start_of_year.year + 1) - timedelta(days=1)
    # Filter OrderProduct objects for the current year
    orders = Order.objects.filter(created_at__range=[start_of_year, end_of_year]).order_by('-created_at')
    # Calculate the sum of order amount for the current year
    total_order_amount = orders.aggregate(total_order_amount=Sum('order_total'))[
                             'total_order_amount'] or 0
    report=[]
    # Define column widths
    serial_width = 10
    order_number_width = 20
    full_name_width = 30
    amount_paid_width = 15
    status_width = 20
    serial_width2 = 50
    # Define the heading
    heading = "Yearly Sales Report"
    # Print the heading
    centered_heading = ' ' * 50+ heading
    textob.textLine( centered_heading)
    textob.textLine(" ")
    textob.textLine(" ")
    # Print column titles
    column_titles = f"{'No.':<{serial_width}}{'Order Number':<{order_number_width}}{'Full Name':<{full_name_width}}{'Amount Paid':<{amount_paid_width}}  {'Status':<{status_width}}"
    textob.textLine(column_titles)
    textob.textLine(" ")
    # Print order information with serial numbers
    for index, order in enumerate(orders, start=1):
    # Concatenate all attributes of the order instance into a single string
     order_info = f"{str(index):<{serial_width}}"
     order_info += f"{str(order.order_number):<{order_number_width}}"
     order_info += f"{order.address.full_name[:full_name_width-4]:<{full_name_width}}"
     order_info += f"{str(order.order_total):<{amount_paid_width}}"
     order_info += f"{order.status[:status_width]:<{status_width}}"
     textob.textLine(order_info) 
    textob.textLine(" ")
    grand_total_label = "Grand Total:"
    grand_total = f"{grand_total_label:<{order_number_width}} {total_order_amount:>{order_number_width}}"
    textob.textLine(grand_total)
    c.drawText(textob)
    c.showPage()
    c.save()
    buf.seek(0)
    return FileResponse(buf,as_attachment=True,filename='yearlyreport.pdf')

def custom_report(request):
      if request.method=="POST":
        starting_date=request.POST['starting_date']
        ending_date=request.POST['ending_date']
        starting_date = datetime.strptime(starting_date, '%Y-%m-%d')
        ending_date = datetime.strptime(ending_date, '%Y-%m-%d')
        ending_date1= ending_date
        ending_date = ending_date + timedelta(days=1)
       
        if starting_date <= ending_date:
           # Fetch orders within the specified date range
           orders = Order.objects.filter(created_at__range=[starting_date, ending_date]).order_by('-created_at')
           # Calculate the sum of order amount for the current year
           total_order_amount = orders.aggregate(total_order_amount=Sum('order_total'))[
                             'total_order_amount'] or 0
           # Calculate the sum of amount_paid for the current day
           total_amount_paid = orders.aggregate(total_amount_paid=Sum('payment__amount_paid'))['total_amount_paid'] or 0
           context = {
            'starting_date' : starting_date,
            'ending_date' :ending_date1,
            'orders': orders,
            'total_order_amount': total_order_amount,
            'total_amount_paid': total_amount_paid,
             }
           return render(request, 'salesreport/custom_report.html', context)
      return render(request,'salesreport/custom_first.html')

def custom_report_pdf(request,starting_date, ending_date):
        buf=io.BytesIO()
        #create canvas
        c=canvas.Canvas(buf,pagesize=letter,bottomup=0)
        #create a text object
        textob=c.beginText()
        textob.setTextOrigin(inch,inch)
        textob.setFont("Helvetica",14)
        starting_date = datetime.strptime(starting_date, '%Y-%m-%d')
        ending_date = datetime.strptime(ending_date, '%Y-%m-%d')
        ending_date = ending_date + timedelta(days=1)
        orders = Order.objects.filter(created_at__range=[starting_date, ending_date]).order_by('-created_at')
        total_order_amount = orders.aggregate(total_order_amount=Sum('order_total'))[
                             'total_order_amount'] or 0
        report=[]
        # Define column widths
        serial_width = 10
        order_number_width = 20
        full_name_width = 30
        amount_paid_width = 15
        status_width = 20
        serial_width2 = 50
        # Define the heading
        heading = "Sales Report"
        # Print the heading
        centered_heading = ' ' * 50+ heading
        textob.textLine( centered_heading)
        textob.textLine(" ")
        textob.textLine(" ")
        # Print column titles
        column_titles = f"{'No.':<{serial_width}}{'Order Number':<{order_number_width}}{'Full Name':<{full_name_width}}{'Amount Paid':<{amount_paid_width}}  {'Status':<{status_width}}"
        textob.textLine(column_titles)
        textob.textLine(" ")
        # Print order information with serial numbers
        for index, order in enumerate(orders, start=1):
        # Concatenate all attributes of the order instance into a single string
            order_info = f"{str(index):<{serial_width}}"
            order_info += f"{str(order.order_number):<{order_number_width}}"
            order_info += f"{order.address.full_name[:full_name_width-4]:<{full_name_width}}"
            order_info += f"{str(order.order_total):<{amount_paid_width}}"
            order_info += f"{order.status[:status_width]:<{status_width}}"
            textob.textLine(order_info) 
        textob.textLine(" ")
        grand_total_label = "Grand Total:"
        grand_total = f"{grand_total_label:<{order_number_width}} {total_order_amount:>{order_number_width}}"
        textob.textLine(grand_total)
        c.drawText(textob)
        c.showPage()
        c.save()
        buf.seek(0)
        return FileResponse(buf,as_attachment=True,filename='customreport.pdf')


@login_required(login_url='login')
def download_invoice(request, order_id):
    buf=io.BytesIO()
    #create canvas
    c=canvas.Canvas(buf,pagesize=letter,bottomup=0)
    #create a text object
    textob=c.beginText()
    textob.setTextOrigin(inch,inch)
    textob.setFont("Helvetica",14)
    heading = "GreatKart"
    centered_heading = ' ' * 50+ heading
    textob.textLine( centered_heading)
    # Print the heading
   
   
    textob.textLine(" ")
    textob.textLine(" ")

    order=Order.objects.get(id=order_id)
    order_detail = OrderProduct.objects.filter(order__order_number=order.order_number)
    
    total_product = []
    subtotal = 0
    for item in order_detail:
        product_total = item.product_price * item.quantity
        subtotal += product_total
        total_product.append({'item': item, 'total': product_total})
    context = {
        'order_detail': total_product,
        'order': order,
        'subtotal': subtotal,
    }
    textob.textLine('                                                                                                    Invoice To')
    textob.textLine('                                                                                                   '+order.address.full_name)
    textob.textLine('                                                                                                   '+order.address.city)
    textob.textLine('                                                                                                   '+order.address.state)
    textob.textLine('                                                                                                   '+order.address.country)
   
    textob.textLine('Order Number:    ' + order.order_number)
    textob.textLine('Transaction ID:   ' + order.payment.payment_id)
    created_date = order.created_at.strftime("%Y-%m-%d %H:%M:%S")
    textob.textLine('Date:                  ' + created_date[:10])
    textob.textLine('Status:                ' + order.status)
   
    textob.textLine(" ")
    textob.textLine(" ")
    textob.textLine(" ")
    serial_width = 10
    order_number_width = 30
    full_name_width = 50
    amount_paid_width = 48
    status_width = 20
    serial_width2 = 50
    column_titles = f"{'Product':<{order_number_width}}{'Quantity':<{full_name_width}}{'Total':<{amount_paid_width}}  "
    textob.textLine(column_titles)   
    textob.textLine(" ")
    # Write product details to the PDF 
    for item in order_detail:
        product_name = item.product.product_name
        quantity = item.quantity
        product_price = item.product_price
        # Concatenate product details into a single string
        product_details = f'{product_name:<{order_number_width}} {quantity:<{ amount_paid_width }} {product_price}'
        # Print the concatenated product details on a single line
        textob.textLine(product_details)
        
    
    textob.textLine(" ")
    textob.textLine(" ")
    textob.textLine('                                                             Total Price: Rs. {}            '.format(subtotal))
    textob.textLine('                                                             Tax: Rs. {}                 '.format(order.tax))
    textob.textLine('                                                             Coupon Discount: Rs. {}            '.format(order.coupon_discount))
    textob.textLine('                                                             Price afetr discount: Rs. {}          '.format(order.order_total))              
    c.drawText(textob)
    c.showPage()
    c.save()
    buf.seek(0)
    return FileResponse(buf,as_attachment=True,filename='Invoice.pdf')


def apply_coupon(request, order_id):
    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code')
        # request.session['coupon_code'] = coupon_code

        try:
            coupon = Coupons.objects.get(coupon_code=coupon_code)
            order = Order.objects.get(id=order_id)
            order.coupon_discount = coupon.discount
            user = request.user

            if coupon.valid_from <= timezone.now() <= coupon.valid_to:
                if order.order_total >= coupon.minimum_amount:
                    if coupon.is_used_by_user(request.user):
                        messages.warning(request, 'Coupon has already been used')
                    else:
                        grand_total = request.session.get('grand_total')
                        updated_total = grand_total - float(coupon.discount)
                        order.order_total = updated_total
                        order.save()
                        total_discount = request.session.get('total_discount')
                        total_discount=total_discount+float(coupon.discount)

                        used_coupons = UserCoupons(user=request.user, coupon=coupon, is_used=True)
                        used_coupons.save()
                        coupon.user=user
                        coupon.is_active=False
                        coupon.save()
                        delivery_charge=100
                        order_address_id = request.session.get('order_address_id')
                        order_address=Address.objects.get(user=request.user,id=order_address_id)
                        cart_items = CartItem.objects.filter(user=request.user)
                        total = request.session.get('total')
                        request.session['grand_total']= updated_total
                        request.session['coupon_discount']=order.coupon_discount
                        request.session['total_discount']=total_discount
                        for item in cart_items:
                            if item.product.offer_percentage:
                             item.total_price = item.quantity * item.product.offer_price
                            else:
                             item.total_price = item.quantity * item.product.price

                        

                        context = {
                                'coupon_discount': order.coupon_discount,
                                'order_address' : order_address,
                                'order': order,
                                'cart_items': cart_items,
                                'total': total,
                                'tax': order.tax,
                                'grand_total': order.order_total,
                                'delivery_charge':delivery_charge,
                                'total_discount':total_discount
                            }
                        return render(request, 'store/place_order.html', context)
                else:
                    messages.warning(request, 'Coupon is not applicable for order total')
            else:
                messages.warning(request, 'Coupon is not applicable for the current date')
        except ObjectDoesNotExist:
            messages.warning(request, 'Coupon code is invalid')
            return render(request, 'store/place_order.html', {'order_id': order_id})
    coupons = Coupons.objects.all()
    user = request.user

    active_coupons = []
    used_coupons = []

    for coupon in coupons:
        is_used = UserCoupons.objects.filter(coupon=coupon, user=user, is_used=True).exists()
        status = "Used" if is_used else "Active"
        if status == "Active":
            active_coupons.append((coupon, status))
        else:
            used_coupons.append((coupon, status))

    # Concatenate active_coupons and used_coupons, with active coupons appearing first
    coupon_data = active_coupons + used_coupons

    
    # Redirect to the place order page if the request method is not POST
    return render(request, 'store/apply_coupon.html',{'order_id': order_id,'coupon_data':coupon_data})


@login_required(login_url='login')
def user_coupon_list(request):
    if request.user.is_authenticated:
        coupons = Coupons.objects.all()
        user = request.user

        active_coupons = []
        used_coupons = []

        for coupon in coupons:
            is_used = UserCoupons.objects.filter(coupon=coupon, user=user, is_used=True).exists()
            status = "Used" if is_used else "Active"
            if status == "Active":
                active_coupons.append((coupon, status))
            else:
                used_coupons.append((coupon, status))

        # Concatenate active_coupons and used_coupons, with active coupons appearing first
        coupon_data = active_coupons + used_coupons
        return render(request, 'accounts/my_coupon.html', {'coupon_data':coupon_data})
    else:
        return redirect('login')
    
def toggle_wallet_flag(request,order_id):
     order = get_object_or_404(Order, id=order_id, user=request.user, is_ordered=False)
     wallet_flag = request.session.get('wallet_flag')
     wallet_flag = not wallet_flag
     request.session['wallet_flag'] = wallet_flag
     order_address_id = request.session.get('order_address_id')
     total = request.session.get('total')
     grand_total = request.session.get('grand_total')
     tax=request.session.get('tax')
     wallet_flag=request.session.get('wallet_flag')
     total_discount=request.session.get('total_discount')
     order_address=Address.objects.get(user=request.user,id=order_address_id)
     cart_items = CartItem.objects.filter(user=request.user)
     delivery_charge=100
     try:
        coupon_discount=request.session.get('coupon_discount')
     except:
        pass
     for item in cart_items:
        if item.product.offer_percentage:
            item.total_price = item.quantity * item.product.offer_price
        else:
            item.total_price = item.quantity * item.product.price
     context = {
        'coupon_discount':coupon_discount,
        'order_address' : order_address,
        'order': order,
        'cart_items': cart_items,
        'total': total,
        'tax': tax,
        'grand_total': grand_total,
        'delivery_charge':delivery_charge,
        'total_discount':total_discount,
        'wallet_flag':wallet_flag
    }
     return render(request, 'store/place_order.html', context)
def paypal_return(request,order_id):
     order = get_object_or_404(Order, id=order_id, user=request.user, is_ordered=False)
     wallet_flag = request.session.get('wallet_flag')
     
     order_address_id = request.session.get('order_address_id')
     total = request.session.get('total')
     grand_total = request.session.get('grand_total')
     tax=request.session.get('tax')
     wallet_flag=request.session.get('wallet_flag')
     total_discount=request.session.get('total_discount')
     order_address=Address.objects.get(user=request.user,id=order_address_id)
     cart_items = CartItem.objects.filter(user=request.user)
     delivery_charge=100
     try:
        coupon_discount=request.session.get('coupon_discount')
     except:
        pass
     for item in cart_items:
        if item.product.offer_percentage:
            item.total_price = item.quantity * item.product.offer_price
        else:
            item.total_price = item.quantity * item.product.price
     context = {
        'coupon_discount':coupon_discount,
        'order_address' : order_address,
        'order': order,
        'cart_items': cart_items,
        'total': total,
        'tax': tax,
        'grand_total': grand_total,
        'delivery_charge':delivery_charge,
        'total_discount':total_discount,
        'wallet_flag':wallet_flag
      }
     message_content = '<div style="background-color: #ffe6e6; border: 1px solid #ff3333; border-radius: 5px; padding: 20px; font-size: 18px; width: 100%; margin: 0 auto;">Something Went wrong.Payment failed. Your order status has been updated to Payment Pending.Try after sometime</div>'
     messages.error(request, mark_safe(message_content))
     return render(request, 'store/place_order.html', context)