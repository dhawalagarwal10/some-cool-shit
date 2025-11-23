import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class Product:
    """represents a product in inventory"""
    sku: str
    name: str
    category: str
    current_stock: int
    unit_cost: float
    selling_price: float
    supplier_lead_time_days: int
    min_order_quantity: int = 10
    storage_cost_per_unit: float = 0.0

@dataclass
class ReorderRecommendation:
    """recommendation for purchase order"""
    sku: str
    product_name: str
    current_stock: int
    reorder_point: int
    recommended_quantity: int
    estimated_stockout_date: Optional[datetime]
    days_until_stockout: Optional[int]
    urgency_level: str  # critical, high, medium, low
    expected_demand_7days: int
    expected_demand_30days: int
    safety_stock: int
    total_cost: float
    reason: str

class InventoryOptimizer:
    """
    calculates optimal reorder points and quantities
    uses forecasted demand, lead times, and safety stock
    """

    def __init__(self, safety_factor: float = 1.5):
        """
        safety_factor: multiplier for safety stock (1.5 = 50% buffer)
        """
        self.safety_factor = safety_factor

    def calculate_safety_stock(
        self,
        avg_daily_demand: float,
        lead_time_days: int,
        demand_std: float
    ) -> int:
        """
        calculate safety stock using standard formula
        accounts for demand variability during lead time
        """
        if demand_std == 0:
            demand_std = avg_daily_demand * 0.2  # assume 20% variation

        # safety stock = Z-score × std dev × sqrt(lead time)
        z_score = 1.65  # 95% service level
        safety_stock = z_score * demand_std * np.sqrt(lead_time_days)

        return int(np.ceil(safety_stock * self.safety_factor))

    def calculate_reorder_point(
        self,
        avg_daily_demand: float,
        lead_time_days: int,
        safety_stock: int
    ) -> int:
        """
        reorder point = (avg daily demand × lead time) + safety stock
        """
        reorder_point = (avg_daily_demand * lead_time_days) + safety_stock
        return int(np.ceil(reorder_point))

    def calculate_economic_order_quantity(
        self,
        annual_demand: float,
        ordering_cost: float,
        holding_cost: float
    ) -> int:
        """
        EOQ = sqrt((2 × annual demand × ordering cost) / holding cost)
        optimal order quantity to minimize total cost
        """
        if holding_cost == 0:
            holding_cost = 0.1  # default 10% of unit cost

        eoq = np.sqrt((2 * annual_demand * ordering_cost) / holding_cost)
        return int(np.ceil(eoq))

    def estimate_stockout_date(
        self,
        current_stock: int,
        forecast_df: pd.DataFrame
    ) -> Tuple[Optional[datetime], Optional[int]]:
        """
        estimate when stock will run out based on forecast
        returns (stockout_date, days_until_stockout)
        """
        if current_stock <= 0:
            return datetime.now(), 0

        cumulative_demand = 0
        for idx, row in forecast_df.iterrows():
            cumulative_demand += row['predicted_demand']
            if cumulative_demand >= current_stock:
                stockout_date = row['date']
                days_until = (stockout_date - datetime.now()).days
                return stockout_date, max(0, days_until)

        return None, None

    def calculate_reorder_quantity(
        self,
        forecast_df: pd.DataFrame,
        current_stock: int,
        reorder_point: int,
        min_order_qty: int,
        lead_time_days: int
    ) -> int:
        """
        calculate how much to order considering:
        - demand during lead time
        - current stock levels
        - minimum order quantities
        """
        # demand during lead time + review period (7 days)
        review_period = 7
        total_period = lead_time_days + review_period

        period_demand = forecast_df.head(total_period)['predicted_demand'].sum()

        # order quantity = expected demand - current stock + safety margin
        order_qty = period_demand - current_stock + reorder_point

        # round up to nearest batch size (e.g., 50 units)
        batch_size = 50
        order_qty = int(np.ceil(order_qty / batch_size) * batch_size)

        # ensure minimum order quantity
        order_qty = max(order_qty, min_order_qty)

        return order_qty

    def determine_urgency(
        self,
        days_until_stockout: Optional[int],
        current_stock: int,
        reorder_point: int
    ) -> str:
        """
        classify urgency level for reorder
        """
        if current_stock == 0:
            return 'critical'

        if days_until_stockout is not None:
            if days_until_stockout <= 3:
                return 'critical'
            elif days_until_stockout <= 7:
                return 'high'
            elif days_until_stockout <= 14:
                return 'medium'

        if current_stock < reorder_point * 0.5:
            return 'high'
        elif current_stock < reorder_point:
            return 'medium'

        return 'low'

    def analyze_product(
        self,
        product: Product,
        forecast_df: pd.DataFrame
    ) -> Optional[ReorderRecommendation]:
        """
        analyze single product and generate reorder recommendation if needed
        """
        try:
            # calculate demand metrics
            avg_daily_demand = forecast_df['predicted_demand'].mean()
            demand_std = forecast_df['predicted_demand'].std()

            if avg_daily_demand == 0:
                logger.warning(f"no demand forecasted for {product.sku}")
                return None

            # calculate inventory parameters
            safety_stock = self.calculate_safety_stock(
                avg_daily_demand,
                product.supplier_lead_time_days,
                demand_std
            )

            reorder_point = self.calculate_reorder_point(
                avg_daily_demand,
                product.supplier_lead_time_days,
                safety_stock
            )

            # estimate stockout timing
            stockout_date, days_until = self.estimate_stockout_date(
                product.current_stock,
                forecast_df
            )

            # determine urgency
            urgency = self.determine_urgency(
                days_until,
                product.current_stock,
                reorder_point
            )

            # calculate expected demand
            demand_7days = int(forecast_df.head(7)['predicted_demand'].sum())
            demand_30days = int(forecast_df.head(30)['predicted_demand'].sum())

            # should we reorder?
            needs_reorder = (
                product.current_stock < reorder_point or
                (days_until is not None and days_until <= 14)
            )

            if not needs_reorder:
                return None

            # calculate order quantity
            order_qty = self.calculate_reorder_quantity(
                forecast_df,
                product.current_stock,
                reorder_point,
                product.min_order_quantity,
                product.supplier_lead_time_days
            )

            # build recommendation reason
            reason = self._build_reason(
                product.current_stock,
                reorder_point,
                days_until,
                stockout_date
            )

            return ReorderRecommendation(
                sku=product.sku,
                product_name=product.name,
                current_stock=product.current_stock,
                reorder_point=reorder_point,
                recommended_quantity=order_qty,
                estimated_stockout_date=stockout_date,
                days_until_stockout=days_until,
                urgency_level=urgency,
                expected_demand_7days=demand_7days,
                expected_demand_30days=demand_30days,
                safety_stock=safety_stock,
                total_cost=order_qty * product.unit_cost,
                reason=reason
            )

        except Exception as e:
            logger.error(f"error analyzing product {product.sku}: {str(e)}")
            return None

    def _build_reason(
        self,
        current_stock: int,
        reorder_point: int,
        days_until: Optional[int],
        stockout_date: Optional[datetime]
    ) -> str:
        """
        generate human-readable reason for recommendation
        """
        if current_stock == 0:
            return "out of stock - immediate reorder required"

        if days_until is not None and days_until <= 7:
            date_str = stockout_date.strftime('%Y-%m-%d')
            return f"stockout predicted on {date_str} ({days_until} days)"

        if current_stock < reorder_point * 0.5:
            return f"current stock ({current_stock}) critically below reorder point ({reorder_point})"

        if current_stock < reorder_point:
            return f"stock level ({current_stock}) below reorder point ({reorder_point})"

        return "preventive reorder based on demand forecast"

    def batch_analyze(
        self,
        products: List[Product],
        forecasts: Dict[str, pd.DataFrame]
    ) -> List[ReorderRecommendation]:
        """
        analyze multiple products and return sorted recommendations
        """
        recommendations = []

        for product in products:
            if product.sku not in forecasts:
                logger.warning(f"no forecast available for {product.sku}")
                continue

            rec = self.analyze_product(product, forecasts[product.sku])
            if rec:
                recommendations.append(rec)

        # sort by urgency and days until stockout
        urgency_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        recommendations.sort(
            key=lambda x: (
                urgency_order[x.urgency_level],
                x.days_until_stockout if x.days_until_stockout is not None else 999
            )
        )

        return recommendations

    def calculate_inventory_metrics(
        self,
        products: List[Product],
        forecasts: Dict[str, pd.DataFrame]
    ) -> Dict[str, any]:
        """
        calculate overall inventory health metrics
        """
        total_value = sum(p.current_stock * p.unit_cost for p in products)
        total_units = sum(p.current_stock for p in products)

        stockout_risks = 0
        low_stock_count = 0

        for product in products:
            if product.sku in forecasts:
                forecast = forecasts[product.sku]
                avg_demand = forecast['predicted_demand'].mean()

                if avg_demand > 0:
                    days_of_stock = product.current_stock / avg_demand

                    if days_of_stock <= 7:
                        stockout_risks += 1
                    elif days_of_stock <= 14:
                        low_stock_count += 1

        return {
            'total_inventory_value': round(total_value, 2),
            'total_units': total_units,
            'products_at_risk': stockout_risks,
            'products_low_stock': low_stock_count,
            'total_products': len(products),
            'health_score': round((1 - (stockout_risks / len(products))) * 100, 1) if products else 0
        }
