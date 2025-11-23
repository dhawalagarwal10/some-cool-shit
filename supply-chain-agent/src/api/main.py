from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import logging

from config.settings import settings
from src.data.connector import InventoryDatabase
from src.core.forecasting import get_forecaster
from src.core.inventory import Product, InventoryOptimizer
from src.core.llm import SupplyChainAgent
from src.utils.helpers import setup_logging, generate_po_number

setup_logging(settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="supply chain intelligence api",
    description="ai-powered inventory optimization and demand forecasting",
    version="1.0.0"
)

# enable cors for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# initialize database
db = InventoryDatabase()

# request/response models
class ProductCreate(BaseModel):
    sku: str
    name: str
    category: str = ""
    current_stock: int = 0
    unit_cost: float = 0
    selling_price: float = 0
    supplier_lead_time_days: int = 7
    min_order_quantity: int = 10

class SalesRecord(BaseModel):
    sku: str
    date: str
    quantity: int
    revenue: float = 0

class ForecastRequest(BaseModel):
    sku: str
    days_ahead: int = 30

class ForecastResponse(BaseModel):
    sku: str
    forecast: List[Dict]
    trend_analysis: Dict
    accuracy_metrics: Optional[Dict] = None

class ReorderAnalysisRequest(BaseModel):
    sku: Optional[str] = None  # if none, analyze all products

class PurchaseOrderCreate(BaseModel):
    sku: str
    quantity: int
    created_by: str = "manual"

@app.get("/")
async def root():
    return {
        "service": "supply chain intelligence api",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected"
    }

@app.post("/products")
async def create_product(product: ProductCreate):
    """
    add a new product to inventory
    """
    try:
        success = db.add_product(product.dict())
        if success:
            return {"message": "product created successfully", "sku": product.sku}
        else:
            raise HTTPException(status_code=400, detail="failed to create product")
    except Exception as e:
        logger.error(f"error creating product: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products")
async def get_products():
    """
    retrieve all products
    """
    try:
        products = db.get_all_products()
        return {"products": products, "total": len(products)}
    except Exception as e:
        logger.error(f"error retrieving products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products/{sku}")
async def get_product(sku: str):
    """
    get details of a specific product
    """
    product = db.get_product(sku)
    if not product:
        raise HTTPException(status_code=404, detail="product not found")
    return product

@app.post("/sales")
async def add_sales_record(sale: SalesRecord):
    """
    record a sales transaction
    """
    try:
        sale_date = datetime.fromisoformat(sale.date)
        db.add_sales_record(sale.sku, sale_date, sale.quantity, sale.revenue)
        return {"message": "sales record added successfully"}
    except Exception as e:
        logger.error(f"error adding sales record: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/sales/{sku}")
async def get_sales_history(sku: str, days: int = 90):
    """
    retrieve sales history for a product
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        sales_df = db.get_sales_history(sku, start_date, end_date)

        if sales_df.empty:
            return {"sku": sku, "sales": [], "message": "no sales history found"}

        sales_data = sales_df.to_dict('records')
        return {
            "sku": sku,
            "sales": sales_data,
            "total_quantity": int(sales_df['quantity'].sum()),
            "avg_daily_sales": round(sales_df['quantity'].mean(), 2)
        }
    except Exception as e:
        logger.error(f"error retrieving sales history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/forecast")
async def generate_forecast(request: ForecastRequest):
    """
    generate demand forecast for a product
    """
    try:
        # get historical sales data
        sales_df = db.get_sales_history(
            request.sku,
            datetime.now() - timedelta(days=180)
        )

        if sales_df.empty:
            raise HTTPException(
                status_code=400,
                detail="insufficient sales history for forecasting"
            )

        # get appropriate forecaster
        forecaster = get_forecaster(sales_df)

        # get product info for category-specific adjustments
        product = db.get_product(request.sku)
        category = product.get('category', '') if product else ''

        # fit and forecast
        forecaster.fit(sales_df, category)
        forecast_df = forecaster.forecast(request.days_ahead)

        # get trend analysis
        trend_info = {}
        accuracy = {}

        if hasattr(forecaster, 'get_trend_analysis'):
            trend_info = forecaster.get_trend_analysis()

        if hasattr(forecaster, 'calculate_forecast_accuracy'):
            accuracy = forecaster.calculate_forecast_accuracy(sales_df)

        return ForecastResponse(
            sku=request.sku,
            forecast=forecast_df.to_dict('records'),
            trend_analysis=trend_info,
            accuracy_metrics=accuracy
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"error generating forecast: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/reorder")
async def analyze_reorders(request: ReorderAnalysisRequest):
    """
    analyze inventory and generate reorder recommendations
    """
    try:
        optimizer = InventoryOptimizer(safety_factor=settings.reorder_safety_factor)

        # get products to analyze
        if request.sku:
            product_data = db.get_product(request.sku)
            if not product_data:
                raise HTTPException(status_code=404, detail="product not found")
            products_data = [product_data]
        else:
            products_data = db.get_all_products()

        # convert to Product objects
        products = []
        forecasts = {}

        for p_data in products_data:
            product = Product(
                sku=p_data['sku'],
                name=p_data['name'],
                category=p_data['category'],
                current_stock=p_data['current_stock'],
                unit_cost=p_data['unit_cost'],
                selling_price=p_data['selling_price'],
                supplier_lead_time_days=p_data['supplier_lead_time_days'],
                min_order_quantity=p_data['min_order_quantity']
            )
            products.append(product)

            # generate forecast for each product
            sales_df = db.get_sales_history(
                p_data['sku'],
                datetime.now() - timedelta(days=90)
            )

            if not sales_df.empty:
                forecaster = get_forecaster(sales_df)
                forecaster.fit(sales_df, p_data['category'])
                forecasts[p_data['sku']] = forecaster.forecast(
                    settings.forecast_horizon_days
                )

        # analyze and get recommendations
        recommendations = optimizer.batch_analyze(products, forecasts)

        # calculate overall metrics
        metrics = optimizer.calculate_inventory_metrics(products, forecasts)

        # convert recommendations to dict
        recs_dict = [
            {
                'sku': r.sku,
                'product_name': r.product_name,
                'current_stock': r.current_stock,
                'reorder_point': r.reorder_point,
                'recommended_quantity': r.recommended_quantity,
                'estimated_stockout_date': r.estimated_stockout_date.isoformat() if r.estimated_stockout_date else None,
                'days_until_stockout': r.days_until_stockout,
                'urgency_level': r.urgency_level,
                'expected_demand_7days': r.expected_demand_7days,
                'expected_demand_30days': r.expected_demand_30days,
                'safety_stock': r.safety_stock,
                'total_cost': r.total_cost,
                'reason': r.reason
            }
            for r in recommendations
        ]

        return {
            "recommendations": recs_dict,
            "total_recommendations": len(recs_dict),
            "inventory_metrics": metrics,
            "generated_at": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"error in reorder analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/purchase-orders")
async def create_purchase_order(po: PurchaseOrderCreate):
    """
    create a purchase order
    """
    try:
        product = db.get_product(po.sku)
        if not product:
            raise HTTPException(status_code=404, detail="product not found")

        po_number = generate_po_number()
        expected_delivery = datetime.now() + timedelta(
            days=product['supplier_lead_time_days']
        )

        po_data = {
            'po_number': po_number,
            'sku': po.sku,
            'quantity': po.quantity,
            'unit_cost': product['unit_cost'],
            'total_cost': po.quantity * product['unit_cost'],
            'expected_delivery_date': expected_delivery.strftime('%Y-%m-%d'),
            'status': 'pending',
            'created_by': po.created_by
        }

        success = db.create_purchase_order(po_data)

        if success:
            return {
                "message": "purchase order created",
                "po_number": po_number,
                "expected_delivery": expected_delivery.isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="failed to create PO")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"error creating purchase order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/purchase-orders")
async def get_purchase_orders():
    """
    retrieve all pending purchase orders
    """
    try:
        orders = db.get_pending_purchase_orders()
        return {"purchase_orders": orders, "total": len(orders)}
    except Exception as e:
        logger.error(f"error retrieving purchase orders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alerts")
async def get_alerts():
    """
    get active inventory alerts
    """
    try:
        alerts = db.get_active_alerts()
        return {"alerts": alerts, "total": len(alerts)}
    except Exception as e:
        logger.error(f"error retrieving alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/insights/executive-summary")
async def generate_executive_summary():
    """
    generate ai-powered executive summary
    """
    try:
        # this requires api keys configured
        if not settings.anthropic_api_key and not settings.openai_api_key:
            raise HTTPException(
                status_code=503,
                detail="llm service not configured"
            )

        agent = SupplyChainAgent(
            provider='anthropic' if settings.anthropic_api_key else 'openai'
        )

        # get current state
        optimizer = InventoryOptimizer()
        products_data = db.get_all_products()

        products = [
            Product(
                sku=p['sku'],
                name=p['name'],
                category=p['category'],
                current_stock=p['current_stock'],
                unit_cost=p['unit_cost'],
                selling_price=p['selling_price'],
                supplier_lead_time_days=p['supplier_lead_time_days'],
                min_order_quantity=p['min_order_quantity']
            )
            for p in products_data
        ]

        # get forecasts
        forecasts = {}
        for p in products_data:
            sales_df = db.get_sales_history(
                p['sku'],
                datetime.now() - timedelta(days=90)
            )
            if not sales_df.empty:
                forecaster = get_forecaster(sales_df)
                forecaster.fit(sales_df)
                forecasts[p['sku']] = forecaster.forecast(30)

        # get recommendations and metrics
        recommendations = optimizer.batch_analyze(products, forecasts)
        metrics = optimizer.calculate_inventory_metrics(products, forecasts)

        # convert to dict for llm
        recs_dict = [
            {
                'product_name': r.product_name,
                'urgency_level': r.urgency_level,
                'days_until_stockout': r.days_until_stockout,
                'total_cost': r.total_cost
            }
            for r in recommendations
        ]

        # generate summary
        summary = agent.generate_executive_summary(
            metrics,
            recs_dict,
            datetime.now()
        )

        return {
            "summary": summary,
            "metrics": metrics,
            "critical_items": len([r for r in recs_dict if r['urgency_level'] == 'critical']),
            "generated_at": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"error generating summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard/overview")
async def dashboard_overview():
    """
    get overview data for dashboard
    """
    try:
        products = db.get_all_products()
        alerts = db.get_active_alerts()
        pending_pos = db.get_pending_purchase_orders()

        total_value = sum(p['current_stock'] * p['unit_cost'] for p in products)
        total_units = sum(p['current_stock'] for p in products)

        critical_alerts = len([a for a in alerts if a['severity'] == 'critical'])

        return {
            "total_products": len(products),
            "total_inventory_value": round(total_value, 2),
            "total_units": total_units,
            "active_alerts": len(alerts),
            "critical_alerts": critical_alerts,
            "pending_purchase_orders": len(pending_pos),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"error getting dashboard overview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
