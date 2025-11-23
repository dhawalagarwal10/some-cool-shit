"""
generate realistic demo data for the supply chain agent
creates products and sales history with realistic patterns
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

from src.data.connector import InventoryDatabase

# fitness/wellness product catalog
PRODUCTS = [
    {
        'sku': 'PROT-WH-1KG',
        'name': 'whey protein isolate 1kg',
        'category': 'supplements',
        'current_stock': 45,
        'unit_cost': 800,
        'selling_price': 1499,
        'supplier_lead_time_days': 5,
        'min_order_quantity': 20,
        'avg_daily_sales': 8,
        'seasonality': 'new_year_peak'
    },
    {
        'sku': 'PROT-CS-1KG',
        'name': 'casein protein 1kg',
        'category': 'supplements',
        'current_stock': 120,
        'unit_cost': 900,
        'selling_price': 1799,
        'supplier_lead_time_days': 5,
        'min_order_quantity': 20,
        'avg_daily_sales': 5,
        'seasonality': 'steady'
    },
    {
        'sku': 'BCAA-500G',
        'name': 'bcaa powder 500g',
        'category': 'supplements',
        'current_stock': 15,
        'unit_cost': 450,
        'selling_price': 899,
        'supplier_lead_time_days': 7,
        'min_order_quantity': 30,
        'avg_daily_sales': 6,
        'seasonality': 'summer_peak'
    },
    {
        'sku': 'CREAT-300G',
        'name': 'creatine monohydrate 300g',
        'category': 'supplements',
        'current_stock': 89,
        'unit_cost': 350,
        'selling_price': 699,
        'supplier_lead_time_days': 5,
        'min_order_quantity': 25,
        'avg_daily_sales': 4,
        'seasonality': 'steady'
    },
    {
        'sku': 'GYMB-5KG',
        'name': 'dumbbell set 5kg',
        'category': 'equipment',
        'current_stock': 8,
        'unit_cost': 600,
        'selling_price': 1299,
        'supplier_lead_time_days': 10,
        'min_order_quantity': 10,
        'avg_daily_sales': 3,
        'seasonality': 'new_year_peak'
    },
    {
        'sku': 'GYMB-10KG',
        'name': 'dumbbell set 10kg',
        'category': 'equipment',
        'current_stock': 25,
        'unit_cost': 1100,
        'selling_price': 2199,
        'supplier_lead_time_days': 10,
        'min_order_quantity': 10,
        'avg_daily_sales': 2,
        'seasonality': 'new_year_peak'
    },
    {
        'sku': 'YMAT-PRO',
        'name': 'premium yoga mat',
        'category': 'equipment',
        'current_stock': 150,
        'unit_cost': 300,
        'selling_price': 799,
        'supplier_lead_time_days': 7,
        'min_order_quantity': 50,
        'avg_daily_sales': 7,
        'seasonality': 'new_year_peak'
    },
    {
        'sku': 'BAND-SET',
        'name': 'resistance band set',
        'category': 'equipment',
        'current_stock': 34,
        'unit_cost': 250,
        'selling_price': 599,
        'supplier_lead_time_days': 7,
        'min_order_quantity': 30,
        'avg_daily_sales': 5,
        'seasonality': 'steady'
    },
    {
        'sku': 'SNAK-PBAR',
        'name': 'protein bars box (12 bars)',
        'category': 'snacks',
        'current_stock': 200,
        'unit_cost': 180,
        'selling_price': 399,
        'supplier_lead_time_days': 3,
        'min_order_quantity': 100,
        'avg_daily_sales': 15,
        'seasonality': 'steady'
    },
    {
        'sku': 'SNAK-NUT',
        'name': 'mixed nuts pack 500g',
        'category': 'snacks',
        'current_stock': 67,
        'unit_cost': 220,
        'selling_price': 499,
        'supplier_lead_time_days': 3,
        'min_order_quantity': 50,
        'avg_daily_sales': 8,
        'seasonality': 'steady'
    },
    {
        'sku': 'BTLL-750ML',
        'name': 'insulated water bottle 750ml',
        'category': 'accessories',
        'current_stock': 180,
        'unit_cost': 200,
        'selling_price': 499,
        'supplier_lead_time_days': 5,
        'min_order_quantity': 40,
        'avg_daily_sales': 10,
        'seasonality': 'summer_peak'
    },
    {
        'sku': 'GLOVE-GYM',
        'name': 'gym gloves pair',
        'category': 'accessories',
        'current_stock': 5,
        'unit_cost': 150,
        'selling_price': 399,
        'supplier_lead_time_days': 7,
        'min_order_quantity': 25,
        'avg_daily_sales': 4,
        'seasonality': 'new_year_peak'
    }
]

def generate_sales_history(product, days=180):
    """
    generate realistic sales history with seasonality and trends
    """
    sales_data = []
    base_demand = product['avg_daily_sales']

    for i in range(days):
        date = datetime.now() - timedelta(days=days - i)

        # base demand with some randomness
        daily_sales = np.random.poisson(base_demand)

        # add seasonality
        month = date.month

        if product['seasonality'] == 'new_year_peak':
            # spike in january-february
            if month in [1, 2]:
                daily_sales = int(daily_sales * 1.8)
            elif month in [11, 12]:
                daily_sales = int(daily_sales * 1.3)

        elif product['seasonality'] == 'summer_peak':
            # spike in may-august
            if month in [5, 6, 7, 8]:
                daily_sales = int(daily_sales * 1.5)

        # add weekly pattern (lower on sundays)
        if date.weekday() == 6:
            daily_sales = int(daily_sales * 0.7)

        # add growth trend (5% monthly growth)
        growth_factor = 1 + (0.05 * (days - i) / 30)
        daily_sales = int(daily_sales / growth_factor)

        # random promotions (20% chance of spike)
        if random.random() < 0.05:
            daily_sales = int(daily_sales * 2)

        # ensure non-negative
        daily_sales = max(0, daily_sales)

        if daily_sales > 0:
            revenue = daily_sales * product['selling_price']
            sales_data.append({
                'sku': product['sku'],
                'date': date.strftime('%Y-%m-%d'),
                'quantity': daily_sales,
                'revenue': revenue
            })

    return sales_data

def populate_database():
    """
    populate database with demo data
    """
    print("initializing database...")
    db = InventoryDatabase()

    print("\nadding products...")
    for product in PRODUCTS:
        # only add core product fields to db
        product_data = {
            'sku': product['sku'],
            'name': product['name'],
            'category': product['category'],
            'current_stock': product['current_stock'],
            'unit_cost': product['unit_cost'],
            'selling_price': product['selling_price'],
            'supplier_lead_time_days': product['supplier_lead_time_days'],
            'min_order_quantity': product['min_order_quantity']
        }

        if db.add_product(product_data):
            print(f"  ✓ added {product['name']}")
        else:
            print(f"  ✗ failed to add {product['name']}")

    print("\ngenerating sales history...")
    all_sales = []

    for product in PRODUCTS:
        sales = generate_sales_history(product, days=180)
        all_sales.extend(sales)
        print(f"  ✓ generated {len(sales)} sales records for {product['name']}")

    print("\nadding sales records to database...")
    for sale in all_sales:
        sale_date = datetime.fromisoformat(sale['date'])
        db.add_sales_record(
            sale['sku'],
            sale_date,
            sale['quantity'],
            sale['revenue']
        )

    print(f"  ✓ added {len(all_sales)} total sales records")

    # create some alerts
    print("\ncreating sample alerts...")
    db.create_alert(
        'GYMB-5KG',
        'low_stock',
        'critical',
        'current stock (8 units) critically low - predicted stockout in 3 days'
    )
    db.create_alert(
        'BCAA-500G',
        'low_stock',
        'high',
        'stock level below reorder point - order recommended'
    )
    db.create_alert(
        'GLOVE-GYM',
        'low_stock',
        'critical',
        'only 5 units remaining - immediate reorder required'
    )

    print("\n✅ demo data generation complete!")
    print("\nquick stats:")
    print(f"  products: {len(PRODUCTS)}")
    print(f"  sales records: {len(all_sales)}")
    print(f"  date range: {min(s['date'] for s in all_sales)} to {max(s['date'] for s in all_sales)}")

    db.close()

def save_to_csv():
    """
    save demo data to csv files for reference
    """
    print("\nsaving data to csv files...")

    # save products
    products_df = pd.DataFrame([
        {
            'sku': p['sku'],
            'name': p['name'],
            'category': p['category'],
            'current_stock': p['current_stock'],
            'unit_cost': p['unit_cost'],
            'selling_price': p['selling_price'],
            'supplier_lead_time_days': p['supplier_lead_time_days'],
            'min_order_quantity': p['min_order_quantity']
        }
        for p in PRODUCTS
    ])
    products_df.to_csv('demo_data/products.csv', index=False)
    print("  ✓ saved products.csv")

    # generate and save sales
    all_sales = []
    for product in PRODUCTS:
        sales = generate_sales_history(product, days=180)
        all_sales.extend(sales)

    sales_df = pd.DataFrame(all_sales)
    sales_df.to_csv('demo_data/sales_history.csv', index=False)
    print("  ✓ saved sales_history.csv")

if __name__ == "__main__":
    print("=" * 60)
    print("supply chain agent - demo data generator")
    print("=" * 60)

    populate_database()
    save_to_csv()

    print("\n" + "=" * 60)
    print("ready to use!")
    print("run the dashboard: streamlit run dashboard/app.py")
    print("=" * 60)
