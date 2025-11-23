# setup guide - step by step

this guide will walk you through setting up and running the supply chain intelligence agent in under 5 minutes.

## prerequisites

- python 3.9 or higher
- pip package manager
- 2gb free disk space

## quick setup (recommended)

### option 1: automated setup (linux/mac)

```bash
cd supply-chain-agent
./run.sh
```

that's it! the script will:
- create virtual environment
- install dependencies
- generate demo data
- launch the dashboard

### option 2: manual setup (all platforms)

#### step 1: create virtual environment

```bash
cd supply-chain-agent
python -m venv venv
```

#### step 2: activate virtual environment

**on linux/mac:**
```bash
source venv/bin/activate
```

**on windows:**
```cmd
venv\Scripts\activate
```

#### step 3: install dependencies

```bash
pip install -r requirements.txt
```

this will install:
- fastapi & uvicorn (api server)
- streamlit (dashboard)
- prophet (forecasting)
- anthropic & openai (ai insights)
- pandas, numpy, plotly (data processing)
- and other required packages

**installation time**: 2-3 minutes

#### step 4: configure environment (optional)

```bash
cp .env.example .env
```

edit `.env` file to add your api keys (optional for demo):

```env
# only needed for ai insights feature
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# only needed for notifications
SLACK_WEBHOOK_URL=your_webhook_here
```

**note**: the system works without api keys, but ai insights won't be available.

#### step 5: generate demo data

```bash
python demo_data/generate_data.py
```

this creates:
- 12 sample products (fitness/wellness items)
- 180 days of realistic sales history
- seasonal patterns and trends
- critical inventory alerts

**generation time**: 5-10 seconds

#### step 6: launch dashboard

```bash
streamlit run dashboard/app.py
```

the dashboard will automatically open in your browser at:
```
http://localhost:8501
```

## exploring the dashboard

### 1. dashboard page

overview of inventory health:
- total products and inventory value
- critical alerts
- inventory levels by product
- recent purchase orders

### 2. inventory page

manage products:
- view all products with filters
- search by name or category
- see detailed product information
- view sales history charts
- add new products

### 3. forecasting page

generate demand predictions:
- select any product
- choose forecast horizon (7-90 days)
- see predicted demand with confidence intervals
- view trend analysis

### 4. recommendations page

get intelligent reorder suggestions:
- click "analyze inventory"
- see prioritized recommendations by urgency
- view detailed calculations (safety stock, reorder point)
- create purchase orders with one click

### 5. insights page

ai-powered analysis (requires api keys):
- executive summaries
- anomaly detection
- forecast explanations in business terms

## running the api (optional)

if you want to use the rest api:

```bash
python src/api/main.py
```

api will be available at:
```
http://localhost:8000
```

api documentation (swagger ui):
```
http://localhost:8000/docs
```

## common issues & solutions

### issue: prophet installation fails

**solution**: install prophet dependencies first

**on mac:**
```bash
brew install cmake
pip install prophet
```

**on linux:**
```bash
sudo apt-get install build-essential
pip install prophet
```

**on windows:**
```cmd
conda install -c conda-forge prophet
```

### issue: port 8501 already in use

**solution**: kill existing streamlit process

```bash
# find process id
lsof -i :8501

# kill process
kill -9 <PID>
```

or specify different port:
```bash
streamlit run dashboard/app.py --server.port 8502
```

### issue: module not found errors

**solution**: ensure virtual environment is activated

check with:
```bash
which python
# should show path to venv/bin/python
```

if not, activate venv:
```bash
source venv/bin/activate  # linux/mac
venv\Scripts\activate     # windows
```

### issue: database locked error

**solution**: close other dashboard instances

only one instance can access sqlite database at a time.

### issue: blank dashboard after launch

**solution**: generate demo data first

```bash
python demo_data/generate_data.py
```

## customizing for your data

### adding your products

#### option 1: via dashboard

1. go to inventory page
2. click "add product" tab
3. fill in product details
4. submit

#### option 2: via csv import

create `my_products.csv`:
```csv
sku,name,category,current_stock,unit_cost,selling_price,supplier_lead_time_days,min_order_quantity
SKU-001,product name,category,100,50,99,7,20
```

then import:
```python
from src.data.connector import InventoryDatabase, CSVDataLoader

db = InventoryDatabase()
CSVDataLoader.load_products('my_products.csv', db)
```

### adding sales history

create `my_sales.csv`:
```csv
sku,date,quantity,revenue
SKU-001,2024-01-01,10,990
SKU-001,2024-01-02,15,1485
```

import:
```python
CSVDataLoader.load_sales_history('my_sales.csv', db)
```

## deployment to production

### deploying dashboard (streamlit cloud)

1. push code to github
2. go to streamlit.io/cloud
3. connect github repo
4. select `dashboard/app.py`
5. add secrets (api keys)
6. deploy

### deploying api (railway/fly.io)

1. create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. deploy:
```bash
# railway
railway up

# or fly.io
fly deploy
```

### using postgresql instead of sqlite

1. install postgresql driver:
```bash
pip install psycopg2-binary
```

2. update `.env`:
```env
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

3. the system will automatically use postgresql

## performance optimization

### for large datasets (1000+ products)

1. **enable caching**: set in `config/settings.py`:
```python
enable_forecast_cache = True
cache_ttl_hours = 24
```

2. **use postgresql**: much faster than sqlite for large data

3. **adjust batch sizes**: in `config/settings.py`:
```python
forecast_batch_size = 50  # process 50 products at a time
```

4. **run analysis as background job**:
```python
# instead of real-time analysis
# schedule daily with cron or celery
```

## monitoring & logs

logs are written to console by default.

to save logs to file:
```bash
streamlit run dashboard/app.py > app.log 2>&1
```

log level can be changed in `.env`:
```env
LOG_LEVEL=DEBUG  # INFO, WARNING, ERROR
```

## getting help

if you encounter issues:

1. check this guide first
2. review README.md for detailed documentation
3. check github issues (if repository is public)
4. review logs for error messages

## next steps

after setup:

1. ✅ explore the demo data
2. ✅ run forecasts on different products
3. ✅ generate reorder recommendations
4. ✅ customize with your own data
5. ✅ configure notifications (slack/email)
6. ✅ set up api keys for ai insights
7. ✅ deploy to production

---

**estimated total setup time**: 5-10 minutes

**system requirements**:
- cpu: 2+ cores
- ram: 4gb minimum
- disk: 2gb free space
- network: internet connection for api calls

enjoy using the supply chain intelligence agent!
