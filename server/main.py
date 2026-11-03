from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import threading
from datetime import date, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field
import mock_data
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders, restocking_orders

app = FastAPI(title="Factory Inventory Management System")

# Quarter mapping for date filtering
QUARTER_MAP = {
    'Q1-2025': ['2025-01', '2025-02', '2025-03'],
    'Q2-2025': ['2025-04', '2025-05', '2025-06'],
    'Q3-2025': ['2025-07', '2025-08', '2025-09'],
    'Q4-2025': ['2025-10', '2025-11', '2025-12']
}

def filter_by_month(items: list, month: Optional[str]) -> list:
    """Filter items by month/quarter based on order_date field"""
    if not month or month == 'all':
        return items

    if month.startswith('Q'):
        # Handle quarters
        if month in QUARTER_MAP:
            months = QUARTER_MAP[month]
            return [item for item in items if any(m in item.get('order_date', '') for m in months)]
    else:
        # Direct month match
        return [item for item in items if month in item.get('order_date', '')]

    return items

def apply_filters(items: list, warehouse: Optional[str] = None, category: Optional[str] = None,
                 status: Optional[str] = None) -> list:
    """Apply common filters to a list of items"""
    filtered = items

    if warehouse and warehouse != 'all':
        filtered = [item for item in filtered if item.get('warehouse') == warehouse]

    if category and category != 'all':
        filtered = [item for item in filtered if item.get('category', '').lower() == category.lower()]

    if status and status != 'all':
        filtered = [item for item in filtered if item.get('status', '').lower() == status.lower()]

    return filtered

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class InventoryItem(BaseModel):
    id: str
    sku: str
    name: str
    category: str
    warehouse: str
    quantity_on_hand: int
    reorder_point: int
    unit_cost: float
    location: str
    last_updated: str

class Order(BaseModel):
    id: str
    order_number: str
    customer: str
    items: List[dict]
    status: str
    order_date: str
    expected_delivery: str
    total_value: float
    actual_delivery: Optional[str] = None
    warehouse: Optional[str] = None
    category: Optional[str] = None

class DemandForecast(BaseModel):
    id: str
    item_sku: str
    item_name: str
    current_demand: int
    forecasted_demand: int
    trend: str
    period: str
    unit_cost: float
    lead_time_days: int

class BacklogItem(BaseModel):
    id: str
    order_id: str
    item_sku: str
    item_name: str
    quantity_needed: int
    quantity_available: int
    days_delayed: int
    priority: str
    has_purchase_order: Optional[bool] = False

class PurchaseOrder(BaseModel):
    id: str
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    status: str
    created_date: str
    notes: Optional[str] = None

class CreatePurchaseOrderRequest(BaseModel):
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    notes: Optional[str] = None

class RestockLine(BaseModel):
    item_sku: str
    quantity: int = Field(gt=0)

class CreateRestockOrderRequest(BaseModel):
    budget: float = Field(gt=0)
    items: List[RestockLine] = Field(min_length=1)

class RestockOrderLine(BaseModel):
    item_sku: str
    item_name: str
    quantity: int
    unit_cost: float
    line_total: float
    lead_time_days: int

class RestockOrder(BaseModel):
    id: str
    order_number: str
    created_date: str
    status: str
    budget: float
    total_cost: float
    lead_time_days: int
    expected_delivery: str
    items: List[RestockOrderLine]

class QuarterlyReport(BaseModel):
    quarter: str
    total_orders: int
    total_revenue: float
    delivered_orders: int
    avg_order_value: float
    fulfillment_rate: float

class MonthlyTrend(BaseModel):
    month: str
    order_count: int
    revenue: float
    delivered_count: int

# API endpoints
@app.get("/")
def root():
    return {"message": "Factory Inventory Management System API", "version": "1.0.0"}

@app.get("/api/inventory", response_model=List[InventoryItem])
def get_inventory(
    warehouse: Optional[str] = None,
    category: Optional[str] = None
):
    """Get all inventory items with optional filtering"""
    return apply_filters(inventory_items, warehouse, category)

@app.get("/api/inventory/{item_id}", response_model=InventoryItem)
def get_inventory_item(item_id: str):
    """Get a specific inventory item"""
    item = next((item for item in inventory_items if item["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.get("/api/orders", response_model=List[Order])
def get_orders(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get all orders with optional filtering"""
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)
    return filtered_orders

@app.get("/api/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    """Get a specific order"""
    order = next((order for order in orders if order["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get("/api/demand", response_model=List[DemandForecast])
def get_demand_forecasts():
    """Get demand forecasts"""
    return demand_forecasts

@app.get("/api/backlog", response_model=List[BacklogItem])
def get_backlog():
    """Get backlog items with purchase order status"""
    # Add has_purchase_order flag to each backlog item
    result = []
    for item in backlog_items:
        item_dict = dict(item)
        # Check if this backlog item has a purchase order
        has_po = any(po["backlog_item_id"] == item["id"] for po in purchase_orders)
        item_dict["has_purchase_order"] = has_po
        result.append(item_dict)
    return result

@app.get("/api/dashboard/summary")
def get_dashboard_summary(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get summary statistics for dashboard with optional filtering"""
    # Filter inventory
    filtered_inventory = apply_filters(inventory_items, warehouse, category)

    # Filter orders
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)

    total_inventory_value = sum(item["quantity_on_hand"] * item["unit_cost"] for item in filtered_inventory)
    low_stock_items = len([item for item in filtered_inventory if item["quantity_on_hand"] <= item["reorder_point"]])
    pending_orders = len([order for order in filtered_orders if order["status"] in ["Processing", "Backordered"]])
    total_backlog_items = len(backlog_items)

    return {
        "total_inventory_value": round(total_inventory_value, 2),
        "low_stock_items": low_stock_items,
        "pending_orders": pending_orders,
        "total_backlog_items": total_backlog_items,
        "total_orders_value": sum(order["total_value"] for order in filtered_orders)
    }

@app.get("/api/spending/summary")
def get_spending_summary():
    """Get spending summary statistics"""
    return spending_summary

@app.get("/api/spending/monthly")
def get_monthly_spending():
    """Get monthly spending breakdown"""
    return monthly_spending

@app.get("/api/spending/categories")
def get_category_spending():
    """Get spending by category"""
    return category_spending

@app.get("/api/spending/transactions")
def get_recent_transactions():
    """Get recent transactions"""
    return recent_transactions

# Serialises number allocation + save: the sync endpoint runs in FastAPI's
# threadpool, so two concurrent POSTs could otherwise claim the same number.
restocking_lock = threading.Lock()

def _next_restock_number() -> int:
    """Next order number, derived from the highest existing one rather than the
    list length so hand-edited/deleted entries in the JSON can't cause reuse."""
    numbers = [int(o["order_number"].split("-")[1]) for o in restocking_orders]
    return max(numbers, default=0) + 1

@app.get("/api/restocking-orders", response_model=List[RestockOrder])
def get_restocking_orders():
    """Get submitted restocking orders, newest first"""
    # Orders are only ever appended, so reversing the list gives newest first.
    return list(reversed(restocking_orders))

@app.post("/api/restocking-orders", response_model=RestockOrder, status_code=201)
def create_restocking_order(request: CreateRestockOrderRequest):
    """Submit a restocking order for demand-forecast items within a budget"""
    forecasts_by_sku = {f["item_sku"]: f for f in demand_forecasts}

    skus = [line.item_sku for line in request.items]
    if len(skus) != len(set(skus)):
        raise HTTPException(status_code=400, detail="Each item may only appear once per order")

    lines = []
    for line in request.items:
        forecast = forecasts_by_sku.get(line.item_sku)
        if not forecast:
            raise HTTPException(status_code=400, detail=f"Unknown item SKU: {line.item_sku}")
        # Prices come from server-side forecast data, never from the client,
        # so a tampered request cannot sneak an order under the budget.
        lines.append({
            "item_sku": forecast["item_sku"],
            "item_name": forecast["item_name"],
            "quantity": line.quantity,
            "unit_cost": forecast["unit_cost"],
            "line_total": round(line.quantity * forecast["unit_cost"], 2),
            "lead_time_days": forecast["lead_time_days"],
        })

    total_cost = round(sum(l["line_total"] for l in lines), 2)
    # Compare in integer cents so float noise (e.g. 3099.6000000001) can never
    # reject an order whose total exactly equals the budget.
    if round(total_cost * 100) > round(request.budget * 100):
        raise HTTPException(
            status_code=400,
            detail=f"Order total {total_cost:.2f} exceeds budget {request.budget:.2f}"
        )

    # The order ships complete, so it is only delivered once its slowest item
    # arrives: the order's lead time is the max across its lines, not the sum.
    lead_time_days = max(l["lead_time_days"] for l in lines)
    today = date.today()

    with restocking_lock:
        next_number = _next_restock_number()
        order = {
            "id": f"rst-{next_number}",
            "order_number": f"RST-{next_number:04d}",
            "created_date": today.isoformat(),
            "status": "Submitted",
            "budget": request.budget,
            "total_cost": total_cost,
            "lead_time_days": lead_time_days,
            "expected_delivery": (today + timedelta(days=lead_time_days)).isoformat(),
            "items": lines,
        }

        # Save first, then commit to memory: if the write fails the client gets
        # a 500 and the in-memory list still matches what is on disk.
        mock_data.save_restocking_orders(restocking_orders + [order])
        restocking_orders.append(order)
    return order

def _filtered_report_orders(warehouse, category, status, month) -> list:
    """Orders after the global filter bar is applied, same rules as /api/orders."""
    filtered = apply_filters(orders, warehouse, category, status)
    return filter_by_month(filtered, month)

def _order_month(order: dict) -> Optional[str]:
    """Return YYYY-MM for an order, or None if order_date is missing or malformed."""
    order_date = order.get('order_date') or ''
    try:
        date.fromisoformat(order_date[:10])
    except ValueError:
        return None
    return order_date[:7]

@app.get("/api/reports/quarterly", response_model=List[QuarterlyReport])
def get_quarterly_reports(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get quarterly performance reports with optional filtering"""
    quarters = {}

    for order in _filtered_report_orders(warehouse, category, status, month):
        order_month = _order_month(order)
        if not order_month:
            continue
        # Derive the quarter from the date instead of a hard-coded 2025 lookup,
        # so data from other years is reported rather than silently dropped.
        year, month_num = int(order_month[:4]), int(order_month[5:7])
        quarter_num = (month_num - 1) // 3 + 1
        key = (year, quarter_num)

        data = quarters.setdefault(key, {
            'quarter': f'Q{quarter_num}-{year}',
            'total_orders': 0,
            'total_revenue': 0.0,
            'delivered_orders': 0,
        })
        data['total_orders'] += 1
        data['total_revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            data['delivered_orders'] += 1

    result = []
    # Sort by (year, quarter) tuple; sorting the "Qn-YYYY" label would put
    # Q1-2026 before Q2-2025.
    for key in sorted(quarters):
        data = quarters[key]
        total = data['total_orders']  # always >= 1 because the bucket exists
        data['avg_order_value'] = round(data['total_revenue'] / total, 2)
        data['fulfillment_rate'] = round(data['delivered_orders'] / total * 100, 1)
        # Round after averaging; summing floats leaves values like 31166853.089999996
        data['total_revenue'] = round(data['total_revenue'], 2)
        result.append(data)
    return result

@app.get("/api/reports/monthly-trends", response_model=List[MonthlyTrend])
def get_monthly_trends(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get month-over-month trends with optional filtering"""
    months = {}

    for order in _filtered_report_orders(warehouse, category, status, month):
        order_month = _order_month(order)
        if not order_month:
            continue

        data = months.setdefault(order_month, {
            'month': order_month,
            'order_count': 0,
            'revenue': 0.0,
            'delivered_count': 0
        })
        data['order_count'] += 1
        data['revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            data['delivered_count'] += 1

    result = [dict(m, revenue=round(m['revenue'], 2)) for m in months.values()]
    result.sort(key=lambda x: x['month'])
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
