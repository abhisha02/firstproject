from django.db import models
from store.models import Product,Variation
from accounts.models import Account
from django.utils import timezone


# Create your models here.
class Cart(models.Model):
  cart_id=models.CharField(max_length=250,blank=True)
  date_added=models.DateField(auto_now_add=True)

  def __str__(self):
    return self.cart_id
  
class CartItem(models.Model):
  user=models.ForeignKey(Account,on_delete=models.CASCADE,null=True)
  product=models.ForeignKey(Product,on_delete=models.CASCADE)
  variations=models.ManyToManyField(Variation,blank=True)
  cart=models.ForeignKey(Cart,on_delete=models.CASCADE,null= True)
  quantity=models.IntegerField()
  is_active=models.BooleanField(default=True)

  def sub_total(self):
    return self.product.price*self.quantity


  def __unicode__(self):
    return self.product
  
class Coupons(models.Model):
    coupon_code = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    minimum_amount = models.IntegerField(default=10000)
    discount = models.IntegerField(default=0)
    is_expired = models.BooleanField(default=False)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    user=models.ForeignKey(Account, on_delete=models.CASCADE, null=True,blank=True)
    is_active=models.BooleanField(default=True)

    def __str__(self):
        return self.coupon_code

    def is_valid(self):
        now = timezone.now()
        if self.valid_to != now:
            self.is_expired = True
            return self.is_expired
        else:
            return self.is_expired

    def is_used_by_user(self, user):
        redeemed_details = UserCoupons.objects.filter(coupon=self, user=user, is_used=True)
        return redeemed_details.exists()
    
class UserCoupons(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)
    coupon = models.ForeignKey(Coupons, on_delete=models.CASCADE)
    is_used = models.BooleanField(default=True)

    def __str__(self):
        return self.coupon.coupon_code