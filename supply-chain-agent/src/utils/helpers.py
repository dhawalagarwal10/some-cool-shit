import logging
from datetime import datetime
from typing import Dict, List
import pandas as pd

def setup_logging(log_level: str = "INFO"):
    """
    configure logging for the application
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def format_currency(amount: float) -> str:
    """
    format number as indian rupees
    """
    return f"₹{amount:,.2f}"

def format_number(num: int) -> str:
    """
    format large numbers with commas
    """
    return f"{num:,}"

def days_to_text(days: int) -> str:
    """
    convert days to human readable text
    """
    if days == 0:
        return "today"
    elif days == 1:
        return "tomorrow"
    elif days < 7:
        return f"{days} days"
    elif days < 30:
        weeks = days // 7
        return f"{weeks} week{'s' if weeks > 1 else ''}"
    else:
        months = days // 30
        return f"{months} month{'s' if months > 1 else ''}"

def urgency_color(urgency: str) -> str:
    """
    get color code for urgency level
    """
    colors = {
        'critical': '#ff0000',
        'high': '#ff6600',
        'medium': '#ffaa00',
        'low': '#00aa00'
    }
    return colors.get(urgency, '#666666')

def urgency_emoji(urgency: str) -> str:
    """
    get emoji for urgency level
    """
    emojis = {
        'critical': '🚨',
        'high': '⚠️',
        'medium': '📊',
        'low': '✅'
    }
    return emojis.get(urgency, '📦')

def calculate_fill_rate(sales_data: pd.DataFrame, stockout_days: int) -> float:
    """
    calculate order fill rate (% of days with stock available)
    """
    if len(sales_data) == 0:
        return 100.0

    total_days = len(sales_data)
    fill_rate = ((total_days - stockout_days) / total_days) * 100
    return round(fill_rate, 2)

def calculate_inventory_turnover(
    avg_inventory: float,
    total_sales: float,
    period_days: int = 365
) -> float:
    """
    calculate inventory turnover ratio
    """
    if avg_inventory == 0:
        return 0

    turnover = total_sales / avg_inventory
    return round(turnover, 2)

def validate_product_data(data: Dict) -> tuple[bool, str]:
    """
    validate product data before saving
    returns (is_valid, error_message)
    """
    required_fields = ['sku', 'name']

    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"missing required field: {field}"

    if 'current_stock' in data and data['current_stock'] < 0:
        return False, "stock cannot be negative"

    if 'unit_cost' in data and data['unit_cost'] < 0:
        return False, "unit cost cannot be negative"

    return True, ""

def generate_po_number() -> str:
    """
    generate unique purchase order number
    """
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"PO-{timestamp}"

def categorize_product_velocity(avg_daily_sales: float) -> str:
    """
    classify product as fast/medium/slow moving
    """
    if avg_daily_sales >= 10:
        return "fast-moving"
    elif avg_daily_sales >= 3:
        return "medium-moving"
    else:
        return "slow-moving"

def detect_seasonality_peaks(sales_df: pd.DataFrame) -> List[str]:
    """
    identify months with seasonal peaks
    """
    if len(sales_df) < 30:
        return []

    sales_df['month'] = pd.to_datetime(sales_df['date']).dt.month
    monthly_avg = sales_df.groupby('month')['quantity'].mean()

    overall_avg = monthly_avg.mean()
    peaks = monthly_avg[monthly_avg > overall_avg * 1.3]

    month_names = {
        1: 'january', 2: 'february', 3: 'march', 4: 'april',
        5: 'may', 6: 'june', 7: 'july', 8: 'august',
        9: 'september', 10: 'october', 11: 'november', 12: 'december'
    }

    return [month_names[m] for m in peaks.index]

def health_score_interpretation(score: float) -> str:
    """
    interpret inventory health score
    """
    if score >= 90:
        return "excellent - inventory well managed"
    elif score >= 75:
        return "good - minor issues to address"
    elif score >= 60:
        return "fair - attention needed"
    else:
        return "poor - immediate action required"
