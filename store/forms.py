from django import forms
from .models import Product,ProductImage,Variation
from carts.models import Coupons
from django.utils import timezone


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['product_name','category','description', 'slug','price', 'stock','image']

class AdditionalImageForm(forms.ModelForm):
    class Meta:
        model=ProductImage
        fields=['addimage']

class VariantForm(forms.ModelForm):
    class Meta:
        model = Variation
        fields = ['variation_category','variation_value','product','stock','image']

class CouponForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super(CouponForm, self).__init__(*args, **kwargs)
        # Set initial value for valid_from and valid_to fields to current datetime
        self.fields['valid_from'].initial = timezone.now()
        self.fields['valid_to'].initial = timezone.now()

    class Meta:
        model = Coupons
        fields = ['coupon_code', 'description', 'minimum_amount', 'discount', 'valid_from', 'valid_to']
        widgets = {
            'valid_from': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'valid_to': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class ProductOfferForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['product_name', 'offer_percentage']

   
    
