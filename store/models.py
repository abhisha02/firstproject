from django.db import models
from category.models import Category,Brand
from django.urls import reverse
from accounts.models import Account

# Create your models here.
class Product(models.Model):
  product_name=models.CharField(max_length=200,unique=True)
  slug=models.SlugField(max_length=200,unique=True)
  description=models.TextField(max_length=500,blank=True)
  price=models.IntegerField()
  image=models.ImageField(upload_to='photos/products')
  image2=models.ImageField(upload_to='photos/products',default='default.jpg',blank=True)
  stock=models.IntegerField()
  is_available=models.BooleanField(default=True)
  category=models.ForeignKey(Category,on_delete=models.CASCADE)
  brand = models.ForeignKey(Brand, on_delete=models.CASCADE, blank=True, null=True)
  created_date=models.DateTimeField(auto_now_add=True)
  modified_date=models.DateTimeField(auto_now_add=True)
  offer_percentage = models.PositiveIntegerField(default=0, blank=True, null=True)
  offer_price = models.PositiveIntegerField(default=0, blank=True, null=True)
  
  def save(self, *args, **kwargs):
        if self.offer_percentage is not None:
            self.offer_price = self.price - (self.price * self.offer_percentage / 100)
        super().save(*args, **kwargs)

  def get_url(self):
    return reverse('product_detail',args=[self.category.slug,self.slug])



  def __str__(self):
    return self.product_name
  
class VariationManager(models.Manager):
  def colors(self):
    return super(VariationManager,self).filter(variation_category='color',is_active=True)
  
  def sizes(self):
    return super(VariationManager,self).filter(variation_category='size',is_active=True)

variation_category_choice=(
  ('color','color'),
  ('size','size')
)
class Variation(models.Model):
  product=models.ForeignKey(Product,on_delete=models.CASCADE)
  variation_category=models.CharField(max_length=100,choices=variation_category_choice)
  variation_value=models.CharField(max_length=100)
  is_active =models.BooleanField(default=True)
  created_date=models.DateTimeField(auto_now_add=True)
  image = models.ImageField(upload_to='photos/products', default='default.jpg')
  stock = models.IntegerField(default=0)

  objects=VariationManager()

  def __str__(self):
    return self.variation_value
  
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    addimage=models.ImageField(upload_to='photos/products')
    addimage2 = models.ImageField(upload_to='photos/products', default='default.jpg', blank=True)

class WishList(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    product = models.ManyToManyField(Product)
    created_at = models.DateTimeField(auto_now_add=True)
