from django.shortcuts import render
from .forms import RegistrationForm,MessageHandler
from django.shortcuts import redirect
from .models import Account
from django.contrib import messages,auth
from .models import Profile
import random
from django.http import HttpResponse
import secrets
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control, never_cache
from django.contrib.auth import authenticate
from django.contrib.auth import logout
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.models import User, Permission, Group




# Create your views here.
#user registration
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@never_cache
def register(request):
  if 'key2' in request.session:
        del request.session['key2']
        return redirect('home')

  if request.method=='POST':
    form=RegistrationForm(request.POST)
    if form.is_valid():
      first_name=form.cleaned_data['first_name']
      last_name=form.cleaned_data['last_name']
      phone_number=form.cleaned_data['phone_number']
      email=form.cleaned_data['email']
      password=form.cleaned_data['password']


    
      user=Account.objects.create_user(first_name=first_name,last_name=last_name,email=email,password=password,phone_number=phone_number)
     
      user.save()
      
      #user activation
      otp = ''.join(secrets.choice('0123456789') for _ in range(4))
      profile=Profile.objects.create(user=user,otp=f'{otp}')
      profile.save()
      user_details = {
            'uid':profile.uid,
            'phone_number':profile.user.phone_number,
            
        }
      request.session['user_details'] = user_details
      request.session['key2']=2
      messagehandler=MessageHandler(request.POST['phone_number'],otp).send_otp_via_message()
      red=redirect(f'otp/{profile.uid}/')
      red.set_cookie("can_otp_enter",True,max_age=30)
      return red  

      messages.success(request,'Registration Sucessful')
      return redirect('register')

  else:
    form=RegistrationForm
  context={
    'form':form
    }
  return render(request,'accounts/register.html',context)

#user login
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@never_cache
def login(request):
  if 'key1' in request.session:
      
      profile = request.session.get('profile')
      context = {'profile': profile}
      return render(request,'home.html',context)

  if request.method == 'POST':
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        # Check if a profile with the given phone number exists
        user=Account.objects.filter(email=email).first()
        if not user:
            messages.error(request, "User does not exist.")
            return redirect('login')
        profile=Profile.objects.get(user=user)
        otp = ''.join(secrets.choice('0123456789') for _ in range(4))
        profile.otp=f'{otp}'
        profile.save()
        
        
        user_details = {
            'uid':profile.uid,
            'phone_number':profile.user.phone_number,
            
           }
        
        request.session['user_details'] = user_details
        
        messagehandler = MessageHandler(profile.user.phone_number, otp).send_otp_via_message()
        red = redirect(f'otp_login/{profile.uid}/')
        red.set_cookie("can_otp_enter",True,max_age=30)
        return red
        
        
  return render(request, 'accounts/login.html')
#login_otp_verify
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@never_cache
def otpVerify_login(request,uid):
    if 'key1' in request.session:
      
      profile = request.session.get('profile')
      context = {'profile': profile}
      return render(request,'home.html',context) 
    
    if request.method == "POST":
        otp = request.POST.get('otp')
        try:
            profile = Profile.objects.filter(uid=uid).first()
        except Profile.DoesNotExist:
            return HttpResponse("Profile not found", status=404)
        
        if request.COOKIES.get('can_otp_enter')!=None:  
            if otp == profile.otp:
                if profile.user is not None:
                
                   profile.user.session = {'profile.user.id': profile.user.id}
                   profile.user.save()
                   profile={
                       'id':profile.id,
                       'first_name':profile.user.first_name
                   }
                   
                   context = {'profile': profile}
                   request.session['profile']=profile
                   request.session['key1']=1
                   return render(request,'home.html',context)
                return redirect('login')
            else:
             messages.error(request, 'You have entered wrong OTP.Try again')
             return redirect(request.path)
        messages.error(request,'30 seconds over.Try again')
        return redirect(request.path)
    return render(request, "accounts/otp_login.html", {'uid': uid})
#login_otp_resend
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@never_cache
def resend_otp_login(request):
 
 if 'resend_otp' in request.POST:
    user_details = request.session.get('user_details')
   
    if user_details:
        # Access user details from the session
             uid = user_details['uid']
             phone_number = user_details['phone_number']
          
             otp = ''.join(secrets.choice('0123456789') for _ in range(4))
             profile = Profile.objects.filter(uid=uid).first()
             profile.otp=otp
             profile.save()
             messagehandler=MessageHandler(profile.user.phone_number,otp).send_otp_via_message()
             red=redirect(f'login/otp_login/{profile.uid}/')
             red.set_cookie("can_otp_enter",True,max_age=30)
             messages.success(request, 'OTP has been resent')
             return red 
    return render(request, 'login.html')
 return render(request, 'accounts/login.html')  






def home1(request):
    if request.COOKIES.get('verified') and request.COOKIES.get('verified')!=None:
        messages.success(request, 'This is a success message.')
        return redirect("register")
    else:
        messages.error(request, 'This is an error message.')
        return redirect("register")


#user registration_otp_verify
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@never_cache
def otpVerify(request,uid):
    if'key3' in request.session:
        return redirect('register')
    if request.method == "POST":
        otp = request.POST.get('otp')
        try:
            profile = Profile.objects.filter(uid=uid).first()
        except Profile.DoesNotExist:
            return HttpResponse("Profile not found", status=404)
        if request.COOKIES.get('can_otp_enter')!=None:  
            if otp == profile.otp:
                if profile.user is not None:
                
                   profile.user.session = {'profile.user.id': profile.user.id}
                   profile.user.save()
                   request.session['key3']=3
                   messages.success(request, 'Your Account has been activated.You can log in now')
                   return redirect("login")
                return redirect('register')
            messages.error(request, 'You have entered wrong OTP.Try again')
            return redirect(request.path)
        messages.error(request,'30 seconds over.Try again')
        return redirect(request.path)
    return render(request, "accounts/otp.html", {'uid': uid})
#userregistration_resend_otp
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@never_cache
def resend_otp(request):
  if 'resend_otp' in request.POST:
    user_details = request.session.get('user_details')
 
    if user_details:
        # Access user details from the session
             uid = user_details['uid']
             phone_number = user_details['phone_number']
          
             otp = ''.join(secrets.choice('0123456789') for _ in range(4))
             profile = Profile.objects.filter(uid=uid).first()
             profile.otp=otp
             profile.save()
             messagehandler=MessageHandler(profile.user.phone_number,otp).send_otp_via_message()
             red=redirect(f'register/otp/{profile.uid}/')
             red.set_cookie("can_otp_enter",True,max_age=30)
             messages.success(request, 'OTP has been resent')
             return red 
    return render(request, 'register.html')
  return render(request, 'accounts/register.html')  

@never_cache
def logout(request):
  if 'key1' in request.session:
        del request.session['key1']
  if 'user_details' in request.session:
        del request.session['user_details']     
  auth.logout(request)
  messages.success(request, 'Lougout Successful')
  return redirect('login')

def dashboard(request):
    return render(request,'accounts/dashboard.html')
