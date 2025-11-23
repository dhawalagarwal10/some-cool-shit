import pandas as pd
import numpy as np
from prophet import Prophet
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class DemandForecaster:
    """
    handles demand forecasting using time series analysis
    combines prophet for trend/seasonality with statistical methods
    """

    def __init__(self, confidence_interval: float = 0.95):
        self.confidence_interval = confidence_interval
        self.model = None
        self.is_fitted = False

    def prepare_data(self, sales_df: pd.DataFrame) -> pd.DataFrame:
        """
        convert sales data to prophet format
        expects columns: date, quantity
        """
        if sales_df.empty:
            raise ValueError("cannot forecast with empty dataset")

        df = sales_df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')

        # aggregate by date in case of multiple entries
        df = df.groupby('date')['quantity'].sum().reset_index()

        # prophet requires specific column names
        df.columns = ['ds', 'y']

        return df

    def detect_seasonality(self, df: pd.DataFrame) -> Dict[str, bool]:
        """
        detect which seasonality patterns exist in the data
        """
        date_range = (df['ds'].max() - df['ds'].min()).days

        patterns = {
            'daily': date_range >= 14,
            'weekly': date_range >= 14,
            'monthly': date_range >= 60,
            'yearly': date_range >= 730  # 2 years
        }

        return patterns

    def fit(self, sales_df: pd.DataFrame, product_category: Optional[str] = None):
        """
        train the forecasting model on historical sales data
        """
        try:
            df = self.prepare_data(sales_df)

            if len(df) < 7:
                raise ValueError(f"need at least 7 days of data, got {len(df)}")

            seasonality = self.detect_seasonality(df)

            # configure prophet based on data characteristics
            self.model = Prophet(
                interval_width=self.confidence_interval,
                daily_seasonality=seasonality['daily'],
                weekly_seasonality=seasonality['weekly'],
                yearly_seasonality=seasonality['yearly'],
                seasonality_mode='multiplicative',  # better for retail
                changepoint_prior_scale=0.05  # adjust for stability
            )

            # add monthly seasonality if data supports it
            if seasonality['monthly']:
                self.model.add_seasonality(
                    name='monthly',
                    period=30.5,
                    fourier_order=5
                )

            # fit new year spike for fitness products
            if product_category and 'fitness' in product_category.lower():
                self.model.add_seasonality(
                    name='new_year_rush',
                    period=365.25,
                    fourier_order=3,
                    prior_scale=10
                )

            self.model.fit(df)
            self.is_fitted = True

            logger.info(f"model trained on {len(df)} data points")

        except Exception as e:
            logger.error(f"failed to fit model: {str(e)}")
            raise

    def forecast(self, days_ahead: int = 30) -> pd.DataFrame:
        """
        generate demand forecast for specified number of days
        returns dataframe with date, predicted demand, and confidence bounds
        """
        if not self.is_fitted:
            raise ValueError("model must be fitted before forecasting")

        future = self.model.make_future_dataframe(periods=days_ahead)
        forecast = self.model.predict(future)

        # extract relevant columns and clean up
        result = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
        result.columns = ['date', 'predicted_demand', 'lower_bound', 'upper_bound']

        # ensure non-negative predictions
        result['predicted_demand'] = result['predicted_demand'].clip(lower=0)
        result['lower_bound'] = result['lower_bound'].clip(lower=0)
        result['upper_bound'] = result['upper_bound'].clip(lower=0)

        # round to whole units
        result['predicted_demand'] = result['predicted_demand'].round()
        result['lower_bound'] = result['lower_bound'].round()
        result['upper_bound'] = result['upper_bound'].round()

        return result

    def calculate_forecast_accuracy(self, actual_df: pd.DataFrame) -> Dict[str, float]:
        """
        calculate accuracy metrics by comparing predictions to actuals
        """
        if not self.is_fitted:
            return {}

        actual = self.prepare_data(actual_df)
        forecast = self.model.predict(actual[['ds']])

        y_true = actual['y'].values
        y_pred = forecast['yhat'].values

        # mean absolute percentage error
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100

        # root mean squared error
        rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))

        # mean absolute error
        mae = np.mean(np.abs(y_true - y_pred))

        return {
            'mape': round(mape, 2),
            'rmse': round(rmse, 2),
            'mae': round(mae, 2)
        }

    def get_trend_analysis(self) -> Dict[str, any]:
        """
        extract trend information from fitted model
        """
        if not self.is_fitted:
            return {}

        # get recent trend direction
        future = self.model.make_future_dataframe(periods=7)
        forecast = self.model.predict(future)

        recent_trend = forecast['trend'].tail(7).values
        trend_direction = 'increasing' if recent_trend[-1] > recent_trend[0] else 'decreasing'
        trend_strength = abs(recent_trend[-1] - recent_trend[0]) / recent_trend[0] * 100

        return {
            'direction': trend_direction,
            'strength_percent': round(trend_strength, 2),
            'current_trend_value': round(recent_trend[-1], 2)
        }


class SimpleMovingAverage:
    """
    fallback forecasting method for products with insufficient data
    uses exponentially weighted moving average
    """

    def __init__(self, window: int = 7):
        self.window = window
        self.avg_demand = 0

    def fit(self, sales_df: pd.DataFrame):
        """
        calculate weighted average from recent sales
        """
        if len(sales_df) == 0:
            self.avg_demand = 0
            return

        # more weight to recent data
        weights = np.exp(np.linspace(-1, 0, len(sales_df)))
        weights = weights / weights.sum()

        self.avg_demand = np.average(sales_df['quantity'], weights=weights)

    def forecast(self, days_ahead: int = 30) -> pd.DataFrame:
        """
        simple projection based on average
        """
        dates = pd.date_range(
            start=datetime.now(),
            periods=days_ahead,
            freq='D'
        )

        # add some variance to make it realistic
        std = self.avg_demand * 0.2
        predictions = np.random.normal(self.avg_demand, std, days_ahead)
        predictions = np.maximum(predictions, 0)  # no negative demand

        return pd.DataFrame({
            'date': dates,
            'predicted_demand': predictions.round(),
            'lower_bound': (predictions * 0.8).round(),
            'upper_bound': (predictions * 1.2).round()
        })


def get_forecaster(sales_df: pd.DataFrame, min_data_points: int = 14) -> any:
    """
    factory function to select appropriate forecaster based on data availability
    """
    if len(sales_df) >= min_data_points:
        return DemandForecaster()
    else:
        logger.warning(f"insufficient data ({len(sales_df)} points), using simple average")
        return SimpleMovingAverage()
