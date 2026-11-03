"""
Mock data for the Factory Inventory Management System
This module loads sample data from JSON files for inventory items, orders, demand forecasts, and backlog items.
All data is from September 2025 and includes warehouse, category, and date fields for filtering.
"""

import json
import os

# Get the directory where this file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

def load_json_file(filename):
    """Load data from a JSON file in the data directory"""
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'r') as f:
        return json.load(f)

# Load all datasets from JSON files
inventory_items = load_json_file('inventory.json')
orders = load_json_file('orders.json')
demand_forecasts = load_json_file('demand_forecasts.json')
backlog_items = load_json_file('backlog_items.json')

# Load spending data
spending_data = load_json_file('spending.json')
spending_summary = spending_data['spending_summary']
monthly_spending = spending_data['monthly_spending']
category_spending = spending_data['category_spending']

# Load transactions
recent_transactions = load_json_file('transactions.json')

# Load purchase orders
purchase_orders = load_json_file('purchase_orders.json')

# Restocking orders are the only data the app writes back to disk. The file is
# gitignored and created on the first submitted order, so a missing file just
# means "no orders yet".
RESTOCKING_ORDERS_FILE = os.path.join(DATA_DIR, 'restocking_orders.json')


def load_restocking_orders(path=None):
    """Load submitted restocking orders, or an empty list if none exist yet."""
    path = path or RESTOCKING_ORDERS_FILE
    if not os.path.exists(path):
        return []
    with open(path, 'r') as f:
        return json.load(f)


def save_restocking_orders(orders_to_save, path=None):
    """Persist restocking orders atomically.

    Writing to a temp file and then os.replace() means a crash mid-write can
    never leave a truncated JSON file that would break the next server start.
    """
    path = path or RESTOCKING_ORDERS_FILE
    tmp_path = path + '.tmp'
    with open(tmp_path, 'w') as f:
        json.dump(orders_to_save, f, indent=2)
    os.replace(tmp_path, path)


restocking_orders = load_restocking_orders()

# All data is now loaded from JSON files in the data/ directory
# This allows for easier maintenance and updates of the sample data
