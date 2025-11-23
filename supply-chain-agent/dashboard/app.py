import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
from pathlib import Path

# add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.data.connector import InventoryDatabase
from src.core.forecasting import get_forecaster
from src.core.inventory import Product, InventoryOptimizer
from src.core.llm import SupplyChainAgent
from src.utils.helpers import (
    format_currency, urgency_color, urgency_emoji,
    days_to_text, health_score_interpretation
)
from config.settings import settings

# page configuration
st.set_page_config(
    page_title="supply chain intelligence",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# custom css
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .urgent-alert {
        background-color: #ffebee;
        padding: 15px;
        border-left: 4px solid #f44336;
        margin: 10px 0;
    }
    .success-alert {
        background-color: #e8f5e9;
        padding: 15px;
        border-left: 4px solid #4caf50;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# initialize database
@st.cache_resource
def get_database():
    return InventoryDatabase()

db = get_database()

# sidebar navigation
st.sidebar.title("📦 supply chain intelligence")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "navigation",
    ["dashboard", "inventory", "forecasting", "recommendations", "insights"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### settings")
auto_refresh = st.sidebar.checkbox("auto refresh", value=False)
if auto_refresh:
    st.sidebar.info("refreshing every 30 seconds")

# main content
if page == "dashboard":
    st.title("📊 inventory dashboard")

    # key metrics row
    col1, col2, col3, col4 = st.columns(4)

    products = db.get_all_products()
    alerts = db.get_active_alerts()

    total_value = sum(p['current_stock'] * p['unit_cost'] for p in products)
    total_units = sum(p['current_stock'] for p in products)
    critical_alerts = len([a for a in alerts if a['severity'] == 'critical'])

    with col1:
        st.metric("total products", len(products))

    with col2:
        st.metric("inventory value", f"₹{total_value:,.0f}")

    with col3:
        st.metric("total units", f"{total_units:,}")

    with col4:
        st.metric("critical alerts", critical_alerts, delta_color="inverse")

    st.markdown("---")

    # inventory health
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("inventory levels by product")

        if products:
            df = pd.DataFrame(products)
            df['value'] = df['current_stock'] * df['unit_cost']

            fig = px.bar(
                df.head(10),
                x='name',
                y='current_stock',
                color='category',
                title='top 10 products by stock level'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("no products in inventory. add products to get started.")

    with col2:
        st.subheader("alerts")

        if alerts:
            for alert in alerts[:5]:
                urgency_icon = urgency_emoji(alert['severity'])
                st.markdown(
                    f"{urgency_icon} **{alert['product_name'] or 'system'}**\n\n{alert['message']}"
                )
        else:
            st.success("no active alerts")

    # recent activity
    st.markdown("---")
    st.subheader("recent purchase orders")

    pos = db.get_pending_purchase_orders()
    if pos:
        po_df = pd.DataFrame(pos)
        st.dataframe(
            po_df[['po_number', 'product_name', 'quantity', 'total_cost', 'status']],
            use_container_width=True
        )
    else:
        st.info("no pending purchase orders")

elif page == "inventory":
    st.title("📦 inventory management")

    tab1, tab2 = st.tabs(["view inventory", "add product"])

    with tab1:
        products = db.get_all_products()

        if products:
            df = pd.DataFrame(products)

            # filters
            col1, col2 = st.columns(2)
            with col1:
                categories = ['all'] + list(df['category'].unique())
                selected_category = st.selectbox("filter by category", categories)

            with col2:
                search = st.text_input("search products")

            # apply filters
            filtered_df = df.copy()
            if selected_category != 'all':
                filtered_df = filtered_df[filtered_df['category'] == selected_category]
            if search:
                filtered_df = filtered_df[
                    filtered_df['name'].str.contains(search, case=False)
                ]

            # display products
            st.dataframe(
                filtered_df[['sku', 'name', 'category', 'current_stock',
                            'unit_cost', 'selling_price']],
                use_container_width=True
            )

            # product details
            st.markdown("---")
            st.subheader("product details")

            selected_sku = st.selectbox(
                "select product",
                filtered_df['sku'].tolist()
            )

            if selected_sku:
                product = db.get_product(selected_sku)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("current stock", product['current_stock'])
                with col2:
                    st.metric("unit cost", f"₹{product['unit_cost']:.2f}")
                with col3:
                    stock_value = product['current_stock'] * product['unit_cost']
                    st.metric("stock value", f"₹{stock_value:,.2f}")

                # sales history chart
                sales_df = db.get_sales_history(
                    selected_sku,
                    datetime.now() - timedelta(days=90)
                )

                if not sales_df.empty:
                    st.subheader("sales history (90 days)")

                    fig = px.line(
                        sales_df,
                        x='date',
                        y='quantity',
                        title='daily sales'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("no sales history available")

        else:
            st.info("no products in inventory")

    with tab2:
        st.subheader("add new product")

        with st.form("add_product_form"):
            col1, col2 = st.columns(2)

            with col1:
                sku = st.text_input("sku *", help="unique product identifier")
                name = st.text_input("product name *")
                category = st.text_input("category")
                current_stock = st.number_input("current stock", min_value=0, value=0)

            with col2:
                unit_cost = st.number_input("unit cost (₹)", min_value=0.0, value=0.0)
                selling_price = st.number_input("selling price (₹)", min_value=0.0, value=0.0)
                lead_time = st.number_input("supplier lead time (days)", min_value=1, value=7)
                min_order = st.number_input("minimum order quantity", min_value=1, value=10)

            submitted = st.form_submit_button("add product")

            if submitted:
                if not sku or not name:
                    st.error("sku and name are required")
                else:
                    product_data = {
                        'sku': sku,
                        'name': name,
                        'category': category,
                        'current_stock': current_stock,
                        'unit_cost': unit_cost,
                        'selling_price': selling_price,
                        'supplier_lead_time_days': lead_time,
                        'min_order_quantity': min_order
                    }

                    if db.add_product(product_data):
                        st.success(f"product {name} added successfully!")
                        st.rerun()
                    else:
                        st.error("failed to add product")

elif page == "forecasting":
    st.title("📈 demand forecasting")

    products = db.get_all_products()

    if not products:
        st.info("add products and sales data to generate forecasts")
    else:
        selected_sku = st.selectbox(
            "select product",
            [p['sku'] for p in products],
            format_func=lambda x: next(p['name'] for p in products if p['sku'] == x)
        )

        days_ahead = st.slider("forecast horizon (days)", 7, 90, 30)

        if st.button("generate forecast"):
            with st.spinner("generating forecast..."):
                try:
                    # get sales history
                    sales_df = db.get_sales_history(
                        selected_sku,
                        datetime.now() - timedelta(days=180)
                    )

                    if sales_df.empty:
                        st.error("insufficient sales history for this product")
                    else:
                        # get forecaster
                        product = db.get_product(selected_sku)
                        forecaster = get_forecaster(sales_df)
                        forecaster.fit(sales_df, product['category'])

                        # generate forecast
                        forecast_df = forecaster.forecast(days_ahead)

                        # display results
                        st.success("forecast generated successfully!")

                        # metrics
                        col1, col2, col3 = st.columns(3)

                        avg_forecast = forecast_df['predicted_demand'].mean()
                        total_forecast = forecast_df['predicted_demand'].sum()

                        with col1:
                            st.metric("average daily demand", f"{avg_forecast:.1f} units")
                        with col2:
                            st.metric("total forecasted demand", f"{int(total_forecast)} units")
                        with col3:
                            if hasattr(forecaster, 'get_trend_analysis'):
                                trend = forecaster.get_trend_analysis()
                                st.metric("trend", trend['direction'])

                        # forecast chart
                        fig = go.Figure()

                        fig.add_trace(go.Scatter(
                            x=forecast_df['date'],
                            y=forecast_df['predicted_demand'],
                            mode='lines',
                            name='forecast',
                            line=dict(color='blue', width=2)
                        ))

                        fig.add_trace(go.Scatter(
                            x=forecast_df['date'],
                            y=forecast_df['upper_bound'],
                            mode='lines',
                            name='upper bound',
                            line=dict(width=0),
                            showlegend=False
                        ))

                        fig.add_trace(go.Scatter(
                            x=forecast_df['date'],
                            y=forecast_df['lower_bound'],
                            mode='lines',
                            name='lower bound',
                            fill='tonexty',
                            line=dict(width=0),
                            fillcolor='rgba(0, 100, 255, 0.2)',
                            showlegend=False
                        ))

                        fig.update_layout(
                            title=f"demand forecast for {product['name']}",
                            xaxis_title="date",
                            yaxis_title="units",
                            height=500
                        )

                        st.plotly_chart(fig, use_container_width=True)

                        # forecast table
                        st.subheader("detailed forecast")
                        st.dataframe(
                            forecast_df.head(14),
                            use_container_width=True
                        )

                except Exception as e:
                    st.error(f"error generating forecast: {str(e)}")

elif page == "recommendations":
    st.title("🎯 reorder recommendations")

    if st.button("analyze inventory"):
        with st.spinner("analyzing inventory..."):
            try:
                optimizer = InventoryOptimizer(safety_factor=settings.reorder_safety_factor)

                # get all products
                products_data = db.get_all_products()

                if not products_data:
                    st.error("no products in inventory")
                else:
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

                        # generate forecast
                        sales_df = db.get_sales_history(
                            p_data['sku'],
                            datetime.now() - timedelta(days=90)
                        )

                        if not sales_df.empty:
                            forecaster = get_forecaster(sales_df)
                            forecaster.fit(sales_df, p_data['category'])
                            forecasts[p_data['sku']] = forecaster.forecast(30)

                    # get recommendations
                    recommendations = optimizer.batch_analyze(products, forecasts)
                    metrics = optimizer.calculate_inventory_metrics(products, forecasts)

                    # display metrics
                    st.subheader("inventory health")

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("health score", f"{metrics['health_score']}%")
                    with col2:
                        st.metric("products at risk", metrics['products_at_risk'])
                    with col3:
                        st.metric("low stock items", metrics['products_low_stock'])
                    with col4:
                        total_value = metrics['total_inventory_value']
                        st.metric("total value", f"₹{total_value:,.0f}")

                    health_msg = health_score_interpretation(metrics['health_score'])
                    st.info(health_msg)

                    # recommendations
                    st.markdown("---")
                    st.subheader(f"reorder recommendations ({len(recommendations)})")

                    if recommendations:
                        for rec in recommendations:
                            urgency_icon = urgency_emoji(rec.urgency_level)
                            color = urgency_color(rec.urgency_level)

                            with st.expander(
                                f"{urgency_icon} {rec.product_name} - {rec.urgency_level.upper()}"
                            ):
                                col1, col2, col3 = st.columns(3)

                                with col1:
                                    st.metric("current stock", rec.current_stock)
                                    st.metric("reorder point", rec.reorder_point)

                                with col2:
                                    st.metric("recommended order", rec.recommended_quantity)
                                    st.metric("total cost", f"₹{rec.total_cost:,.2f}")

                                with col3:
                                    if rec.days_until_stockout:
                                        st.metric(
                                            "stockout in",
                                            days_to_text(rec.days_until_stockout)
                                        )
                                    st.metric("7-day demand", rec.expected_demand_7days)

                                st.markdown(f"**reason:** {rec.reason}")

                                if st.button(f"create purchase order", key=f"po_{rec.sku}"):
                                    # create po
                                    product = db.get_product(rec.sku)
                                    expected_delivery = datetime.now() + timedelta(
                                        days=product['supplier_lead_time_days']
                                    )

                                    po_data = {
                                        'sku': rec.sku,
                                        'quantity': rec.recommended_quantity,
                                        'unit_cost': product['unit_cost'],
                                        'total_cost': rec.total_cost,
                                        'expected_delivery_date': expected_delivery.strftime('%Y-%m-%d'),
                                        'created_by': 'dashboard'
                                    }

                                    if db.create_purchase_order(po_data):
                                        st.success("purchase order created!")
                                    else:
                                        st.error("failed to create purchase order")
                    else:
                        st.success("all products are well-stocked!")

            except Exception as e:
                st.error(f"error analyzing inventory: {str(e)}")

elif page == "insights":
    st.title("🤖 ai insights")

    if not settings.anthropic_api_key and not settings.openai_api_key:
        st.warning("configure api keys in .env file to use ai insights")
    else:
        if st.button("generate executive summary"):
            with st.spinner("generating ai insights..."):
                try:
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

                    # convert to dict
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

                    st.markdown("### executive summary")
                    st.markdown(summary)

                except Exception as e:
                    st.error(f"error generating insights: {str(e)}")

# auto refresh
if auto_refresh:
    import time
    time.sleep(30)
    st.rerun()
