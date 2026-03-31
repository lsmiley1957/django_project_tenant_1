import json
import os
from decimal import Decimal, InvalidOperation
from django.conf import settings
from .models import Category, Supplier, Product, StockTransaction


class TenantDataSeeder:
    def __init__(self, business_type):
        self.business_type = business_type
        # Finds the JSON file relative to this script
        self.seed_file = os.path.join(
            os.path.dirname(__file__),
            'data_seeds',
            f"{business_type}_seed.json"
        )

    def run(self):
        if not os.path.exists(self.seed_file):
            print(f"Error: {self.seed_file} not found.")
            return False

        try:
            with open(self.seed_file, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return False

        # --- 1. Seed Categories ---
        category_map = {}
        for cat_data in data.get('categories', []):
            cat, _ = Category.objects.get_or_create(
                name=cat_data['name'].strip(),
                defaults={'description': cat_data.get('description', '')}
            )
            category_map[cat.name] = cat

        # --- 2. Seed Suppliers ---
        supplier_map = {}
        for sup_data in data.get('suppliers', []):
            sup, _ = Supplier.objects.get_or_create(
                name=sup_data['name'].strip(),
                defaults={
                    'contact_email': sup_data.get('contact_email', ''),
                    'average_lead_time': sup_data.get('average_lead_time', 0)
                }
            )
            supplier_map[sup.name] = sup

        # --- 3. Seed Products ---
        products_created = 0
        for prod_data in data.get('products', []):
            try:
                # Use .strip() to ensure no accidental whitespace causes a mismatch
                cat_name = prod_data.get('category_name', '').strip()
                sup_name = prod_data.get('supplier_name', '').strip()

                category = category_map.get(cat_name)
                supplier = supplier_map.get(sup_name)

                if not category or not supplier:
                    print(
                        f"Skipping Product {prod_data.get('sku')}: Missing Category ({cat_name}) or Supplier ({sup_name})")
                    continue

                # Safely handle Decimal conversion
                try:
                    cost = Decimal(str(prod_data.get('cost_price', '0.00')))
                    sale = Decimal(str(prod_data.get('sale_price', '0.00')))
                except (InvalidOperation, ValueError):
                    cost = Decimal('0.00')
                    sale = Decimal('0.00')

                product, created = Product.objects.get_or_create(
                    sku=prod_data['sku'].strip(),
                    defaults={
                        'name': prod_data['name'],
                        'category': category,
                        'supplier': supplier,
                        'cost_price': cost,
                        'sale_price': sale,
                        'quantity_in_stock': prod_data.get('quantity_in_stock', 0),
                        'reorder_level': prod_data.get('reorder_level', 10),
                        'location': prod_data.get('location', ''),
                        'expiry_date': prod_data.get('expiry_date'),
                    }
                )

                # --- 4. Create Audit Trail ---
                if created and product.quantity_in_stock > 0:
                    StockTransaction.objects.create(
                        product=product,
                        change=product.quantity_in_stock,
                        type='RESTOCK',
                        notes="Initial inventory seed"
                    )

                products_created += 1

            except Exception as prod_err:
                print(f"Failed to seed product {prod_data.get('sku')}: {prod_err}")

        print(f"Seeding completed: {products_created} products processed for {self.business_type}.")
        return True