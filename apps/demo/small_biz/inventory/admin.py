from django.contrib import admin
from .models import Product, Category, Supplier


admin.site.register(Supplier)


admin.site.register(Product)


admin.site.register(Category)