import anthropic
import openai
from typing import Dict, List, Optional
import json
import logging
from datetime import datetime
from config.settings import settings

logger = logging.getLogger(__name__)

class SupplyChainAgent:
    """
    llm-powered agent for contextual supply chain insights
    analyzes data and provides strategic recommendations
    """

    def __init__(self, provider: str = 'anthropic'):
        """
        provider: 'anthropic' or 'openai'
        """
        self.provider = provider

        if provider == 'anthropic':
            self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            self.model = 'claude-3-5-sonnet-20241022'
        else:
            self.client = openai.OpenAI(api_key=settings.openai_api_key)
            self.model = 'gpt-4-turbo-preview'

    def _call_llm(self, prompt: str, system_prompt: str) -> str:
        """
        make llm api call based on provider
        """
        try:
            if self.provider == 'anthropic':
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text

            else:  # openai
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2000
                )
                return response.choices[0].message.content

        except Exception as e:
            logger.error(f"llm call failed: {str(e)}")
            return "unable to generate insights at this time"

    def analyze_reorder_recommendation(
        self,
        product_name: str,
        current_stock: int,
        recommended_qty: int,
        urgency: str,
        forecast_data: Dict,
        historical_context: Optional[Dict] = None
    ) -> str:
        """
        get llm analysis of a specific reorder recommendation
        """
        system_prompt = """you are a supply chain analyst for a fitness/wellness company.
analyze inventory data and provide actionable insights in a concise, business-focused manner.
focus on: risk assessment, cost implications, and strategic recommendations.
be direct and avoid unnecessary elaboration."""

        context_str = ""
        if historical_context:
            context_str = f"\nhistorical context: {json.dumps(historical_context, indent=2)}"

        prompt = f"""analyze this reorder situation:

product: {product_name}
current stock: {current_stock} units
recommended order: {recommended_qty} units
urgency: {urgency}
expected demand (7 days): {forecast_data.get('demand_7days', 0)}
expected demand (30 days): {forecast_data.get('demand_30days', 0)}
{context_str}

provide:
1. risk assessment (2-3 sentences)
2. cost-benefit analysis
3. specific recommendation (approve/modify/delay)
4. any seasonal or market factors to consider

keep it under 200 words."""

        return self._call_llm(prompt, system_prompt)

    def generate_executive_summary(
        self,
        inventory_metrics: Dict,
        recommendations: List[Dict],
        date: datetime
    ) -> str:
        """
        create daily executive summary for leadership
        """
        system_prompt = """you are an executive assistant preparing daily inventory briefings
for a fast-growing fitness company's leadership team. be concise, highlight risks and opportunities,
and provide clear action items. use business language, not technical jargon."""

        critical_items = [r for r in recommendations if r['urgency_level'] == 'critical']
        high_priority = [r for r in recommendations if r['urgency_level'] == 'high']

        total_po_value = sum(r['total_cost'] for r in recommendations)

        prompt = f"""generate executive summary for {date.strftime('%Y-%m-%d')}:

inventory health:
- total value: ${inventory_metrics.get('total_inventory_value', 0):,.2f}
- health score: {inventory_metrics.get('health_score', 0)}%
- products at risk: {inventory_metrics.get('products_at_risk', 0)}
- total products: {inventory_metrics.get('total_products', 0)}

reorder recommendations:
- critical priority: {len(critical_items)} items
- high priority: {len(high_priority)} items
- total recommended po value: ${total_po_value:,.2f}

critical products:
{json.dumps([{'name': r['product_name'], 'days_until_stockout': r['days_until_stockout']} for r in critical_items[:5]], indent=2)}

provide:
1. overall situation assessment (2-3 sentences)
2. immediate actions needed
3. financial impact summary
4. any concerning trends

format as a brief email. under 250 words."""

        return self._call_llm(prompt, system_prompt)

    def detect_anomalies(
        self,
        product_name: str,
        recent_sales: List[int],
        forecast: List[int]
    ) -> Optional[str]:
        """
        identify unusual patterns in sales data
        """
        # quick statistical check first
        avg_sales = sum(recent_sales) / len(recent_sales) if recent_sales else 0
        std_sales = (sum((x - avg_sales) ** 2 for x in recent_sales) / len(recent_sales)) ** 0.5 if recent_sales else 0

        recent_avg = sum(recent_sales[-7:]) / 7 if len(recent_sales) >= 7 else avg_sales

        # only call llm if anomaly detected
        if abs(recent_avg - avg_sales) > 2 * std_sales:

            system_prompt = """you are a data analyst specializing in retail patterns.
identify and explain anomalies in sales data concisely."""

            prompt = f"""detected unusual pattern for {product_name}:

recent 7-day average: {recent_avg:.1f} units/day
historical average: {avg_sales:.1f} units/day
standard deviation: {std_sales:.1f}

recent sales: {recent_sales[-14:]}
forecasted: {forecast[:7]}

explain what might be happening and suggest investigation areas.
keep it under 100 words."""

            return self._call_llm(prompt, system_prompt)

        return None

    def optimize_purchase_strategy(
        self,
        recommendations: List[Dict],
        budget_constraint: Optional[float] = None,
        warehouse_capacity: Optional[int] = None
    ) -> Dict[str, any]:
        """
        help prioritize and optimize purchase orders given constraints
        """
        system_prompt = """you are a procurement strategist. optimize purchase decisions
considering budget limits, urgency, and business impact. provide clear prioritization."""

        total_cost = sum(r['total_cost'] for r in recommendations)
        total_units = sum(r['recommended_quantity'] for r in recommendations)

        constraints_str = ""
        if budget_constraint:
            constraints_str += f"\nbudget limit: ${budget_constraint:,.2f}"
        if warehouse_capacity:
            constraints_str += f"\nwarehouse capacity: {warehouse_capacity} units"

        prompt = f"""optimize these {len(recommendations)} purchase orders:

total cost: ${total_cost:,.2f}
total units: {total_units}
{constraints_str}

recommendations by urgency:
{json.dumps([{'product': r['product_name'], 'qty': r['recommended_quantity'],
'cost': r['total_cost'], 'urgency': r['urgency_level'],
'days_until_stockout': r['days_until_stockout']} for r in recommendations[:10]], indent=2)}

provide:
1. which orders to approve immediately
2. which can be deferred or reduced
3. optimized spending allocation
4. risk mitigation for deprioritized items

format as json with keys: immediate_orders (list), deferred_orders (list),
total_optimized_cost (number), rationale (string)"""

        response = self._call_llm(prompt, system_prompt)

        try:
            # attempt to parse json response
            result = json.loads(response)
            return result
        except:
            # fallback if llm doesn't return valid json
            return {
                'immediate_orders': [r['product_name'] for r in recommendations if r['urgency_level'] in ['critical', 'high']],
                'deferred_orders': [r['product_name'] for r in recommendations if r['urgency_level'] in ['medium', 'low']],
                'total_optimized_cost': sum(r['total_cost'] for r in recommendations if r['urgency_level'] in ['critical', 'high']),
                'rationale': response
            }

    def explain_forecast(
        self,
        product_name: str,
        forecast_data: Dict,
        trend_info: Dict
    ) -> str:
        """
        explain forecast results in business terms
        """
        system_prompt = """you are a business analyst explaining forecasts to non-technical stakeholders.
translate statistical predictions into actionable business insights."""

        prompt = f"""explain this demand forecast for {product_name}:

trend: {trend_info.get('direction', 'stable')} ({trend_info.get('strength_percent', 0):.1f}% change)
predicted demand (30 days): {forecast_data.get('predicted_demand', 0)} units
confidence interval: {forecast_data.get('lower_bound', 0)} - {forecast_data.get('upper_bound', 0)} units

context: fitness/wellness product in bangalore market

explain:
1. what's driving this trend
2. confidence in the forecast
3. business implications
4. suggested inventory strategy

under 150 words, in simple business language."""

        return self._call_llm(prompt, system_prompt)


class InsightCache:
    """
    simple cache to avoid redundant llm calls
    """

    def __init__(self, ttl_seconds: int = 3600):
        self.cache = {}
        self.ttl = ttl_seconds

    def get(self, key: str) -> Optional[str]:
        if key in self.cache:
            value, timestamp = self.cache[key]
            if (datetime.now() - timestamp).seconds < self.ttl:
                return value
            else:
                del self.cache[key]
        return None

    def set(self, key: str, value: str):
        self.cache[key] = (value, datetime.now())

    def clear(self):
        self.cache = {}
