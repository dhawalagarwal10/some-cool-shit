import pandas as pd
import sqlite3
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class InventoryDatabase:
    """
    handles database operations for inventory data
    supports sqlite for demo, easily extensible to postgres
    """

    def __init__(self, db_path: str = "inventory.db"):
        self.db_path = db_path
        self.conn = None
        self._init_database()

    def _init_database(self):
        """
        create tables if they don't exist
        """
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)

        # products table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                sku TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT,
                current_stock INTEGER DEFAULT 0,
                unit_cost REAL DEFAULT 0,
                selling_price REAL DEFAULT 0,
                supplier_lead_time_days INTEGER DEFAULT 7,
                min_order_quantity INTEGER DEFAULT 10,
                storage_cost_per_unit REAL DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # sales history table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS sales_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT NOT NULL,
                date DATE NOT NULL,
                quantity INTEGER NOT NULL,
                revenue REAL,
                FOREIGN KEY (sku) REFERENCES products (sku)
            )
        """)

        # purchase orders table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS purchase_orders (
                po_number TEXT PRIMARY KEY,
                sku TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_cost REAL,
                total_cost REAL,
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expected_delivery_date DATE,
                status TEXT DEFAULT 'pending',
                created_by TEXT DEFAULT 'system',
                FOREIGN KEY (sku) REFERENCES products (sku)
            )
        """)

        # alerts table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT,
                alert_type TEXT,
                severity TEXT,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved BOOLEAN DEFAULT 0
            )
        """)

        self.conn.commit()
        logger.info("database initialized")

    def add_product(self, product_data: Dict) -> bool:
        """
        add or update product in database
        """
        try:
            self.conn.execute("""
                INSERT OR REPLACE INTO products
                (sku, name, category, current_stock, unit_cost, selling_price,
                 supplier_lead_time_days, min_order_quantity, storage_cost_per_unit)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                product_data['sku'],
                product_data['name'],
                product_data.get('category', ''),
                product_data.get('current_stock', 0),
                product_data.get('unit_cost', 0),
                product_data.get('selling_price', 0),
                product_data.get('supplier_lead_time_days', 7),
                product_data.get('min_order_quantity', 10),
                product_data.get('storage_cost_per_unit', 0)
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"failed to add product: {str(e)}")
            return False

    def get_product(self, sku: str) -> Optional[Dict]:
        """
        retrieve product by sku
        """
        cursor = self.conn.execute(
            "SELECT * FROM products WHERE sku = ?",
            (sku,)
        )
        row = cursor.fetchone()

        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None

    def get_all_products(self) -> List[Dict]:
        """
        get all products from database
        """
        cursor = self.conn.execute("SELECT * FROM products")
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def add_sales_record(self, sku: str, date: datetime, quantity: int, revenue: float = 0):
        """
        record a sales transaction
        """
        try:
            self.conn.execute("""
                INSERT INTO sales_history (sku, date, quantity, revenue)
                VALUES (?, ?, ?, ?)
            """, (sku, date.strftime('%Y-%m-%d'), quantity, revenue))
            self.conn.commit()
        except Exception as e:
            logger.error(f"failed to add sales record: {str(e)}")

    def get_sales_history(
        self,
        sku: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        retrieve sales history for a product
        """
        query = "SELECT date, quantity FROM sales_history WHERE sku = ?"
        params = [sku]

        if start_date:
            query += " AND date >= ?"
            params.append(start_date.strftime('%Y-%m-%d'))

        if end_date:
            query += " AND date <= ?"
            params.append(end_date.strftime('%Y-%m-%d'))

        query += " ORDER BY date"

        df = pd.read_sql_query(query, self.conn, params=params)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
        return df

    def create_purchase_order(self, po_data: Dict) -> bool:
        """
        create a new purchase order
        """
        try:
            po_number = po_data.get('po_number', f"PO-{datetime.now().strftime('%Y%m%d-%H%M%S')}")

            self.conn.execute("""
                INSERT INTO purchase_orders
                (po_number, sku, quantity, unit_cost, total_cost,
                 expected_delivery_date, status, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                po_number,
                po_data['sku'],
                po_data['quantity'],
                po_data.get('unit_cost', 0),
                po_data.get('total_cost', 0),
                po_data.get('expected_delivery_date'),
                po_data.get('status', 'pending'),
                po_data.get('created_by', 'system')
            ))
            self.conn.commit()
            logger.info(f"created purchase order {po_number}")
            return True
        except Exception as e:
            logger.error(f"failed to create PO: {str(e)}")
            return False

    def get_pending_purchase_orders(self) -> List[Dict]:
        """
        get all pending purchase orders
        """
        cursor = self.conn.execute("""
            SELECT po.*, p.name as product_name
            FROM purchase_orders po
            JOIN products p ON po.sku = p.sku
            WHERE po.status = 'pending'
            ORDER BY po.order_date DESC
        """)
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def create_alert(self, sku: str, alert_type: str, severity: str, message: str):
        """
        create an inventory alert
        """
        try:
            self.conn.execute("""
                INSERT INTO alerts (sku, alert_type, severity, message)
                VALUES (?, ?, ?, ?)
            """, (sku, alert_type, severity, message))
            self.conn.commit()
        except Exception as e:
            logger.error(f"failed to create alert: {str(e)}")

    def get_active_alerts(self) -> List[Dict]:
        """
        get unresolved alerts
        """
        cursor = self.conn.execute("""
            SELECT a.*, p.name as product_name
            FROM alerts a
            LEFT JOIN products p ON a.sku = p.sku
            WHERE a.resolved = 0
            ORDER BY a.created_at DESC
        """)
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def update_stock(self, sku: str, new_stock: int):
        """
        update current stock level
        """
        try:
            self.conn.execute("""
                UPDATE products
                SET current_stock = ?, last_updated = CURRENT_TIMESTAMP
                WHERE sku = ?
            """, (new_stock, sku))
            self.conn.commit()
        except Exception as e:
            logger.error(f"failed to update stock: {str(e)}")

    def close(self):
        """
        close database connection
        """
        if self.conn:
            self.conn.close()


class CSVDataLoader:
    """
    load inventory and sales data from csv files
    useful for importing existing data
    """

    @staticmethod
    def load_products(csv_path: str, db: InventoryDatabase) -> int:
        """
        load products from csv file
        expected columns: sku, name, category, current_stock, unit_cost, selling_price
        """
        try:
            df = pd.read_csv(csv_path)
            count = 0

            for _, row in df.iterrows():
                product_data = row.to_dict()
                if db.add_product(product_data):
                    count += 1

            logger.info(f"loaded {count} products from {csv_path}")
            return count
        except Exception as e:
            logger.error(f"failed to load products: {str(e)}")
            return 0

    @staticmethod
    def load_sales_history(csv_path: str, db: InventoryDatabase) -> int:
        """
        load sales history from csv
        expected columns: sku, date, quantity, revenue
        """
        try:
            df = pd.read_csv(csv_path)
            df['date'] = pd.to_datetime(df['date'])
            count = 0

            for _, row in df.iterrows():
                db.add_sales_record(
                    row['sku'],
                    row['date'],
                    int(row['quantity']),
                    float(row.get('revenue', 0))
                )
                count += 1

            logger.info(f"loaded {count} sales records from {csv_path}")
            return count
        except Exception as e:
            logger.error(f"failed to load sales history: {str(e)}")
            return 0
