# AgriConnect

AgriConnect is a Django and Django REST Framework backend for connecting farmers and wholesalers through agricultural inventory, listings, bidding, orders, and price-prediction workflows.

The project provides:

- Farmer and wholesaler registration and authentication
- JWT access, refresh, and logout endpoints
- Farmer crop stock and marketplace listings
- Wholesaler inventory and stock management
- Real-time bidding support with Django Channels and Redis
- Order and payment-status workflows
- Crop, state, district, commodity, variety, grade, and market master data
- Agricultural commodity price prediction using historical mandi prices and weather features
- OpenAPI schema, Swagger UI, and ReDoc documentation
- Optional S3-backed media and static-file storage

## Technology stack

- Python
- Django
- Django REST Framework
- Django Channels and Daphne
- MySQL
- Redis
- Simple JWT
- drf-spectacular
- scikit-learn, XGBoost, LightGBM, pandas, and NumPy
- NASA POWER weather API
- data.gov.in mandi-price API
- Amazon S3-compatible storage

## Project structure

```text
aggriconnect/
├── Admin/             # Custom admin user, authentication, and master-data APIs
├── farmer/            # Farmer accounts, stock, listings, and price predictions
├── wholesaler/        # Wholesaler accounts, stock, bidding, and orders
├── price_predictor/   # Feature preparation, external data access, training, and inference
├── aggriconnect/      # Django project settings, URL configuration, ASGI, and storage
├── dataset/           # Supporting datasets such as district coordinates
├── ml_models/         # Persisted trained model pipeline
├── photos/            # Local media files for development
├── manage.py
├── requirements.txt
└── schema.yml         # OpenAPI schema
```

## Prerequisites

Install the following before running the project:

- Python 3.11 or a compatible Python version supported by the pinned dependencies
- MySQL Server
- Redis Server
- A data.gov.in API key for live mandi-price features
- AWS S3 credentials if S3 storage is enabled

The application is configured for MySQL and Redis by default. Update the configuration for other environments before deployment.

## Installation

From this directory:

```powershell
cd aggriconnect
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

On Windows, if PowerShell blocks script activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Environment configuration

Create a `.env` file in the `aggriconnect/` directory. Do not commit this file.

```dotenv
DB_NAME=aggriconnect
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306
DATA_GOV_API_KEY=your_data_gov_api_key

# Required only when using S3 storage
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_STORAGE_BUCKET_NAME=your_bucket_name
```

Create the MySQL database before running migrations:

```sql
CREATE DATABASE aggriconnect CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Redis must be available at `127.0.0.1:6379` unless the Django settings are changed.

## Database setup

Run migrations and create an administrative user:

```powershell
python manage.py migrate
python manage.py createsuperuser
```

Load or create the required master data for crops, states, districts, commodities, varieties, grades, and markets before using the marketplace endpoints.

## Running the development server

For standard HTTP API development:

```powershell
python manage.py runserver
```

To run the ASGI application with WebSocket support:

```powershell
daphne aggriconnect.asgi:application
```

The API is then available at `http://127.0.0.1:8000/`.

## API endpoints

All API paths are grouped under the following prefixes:

| Area | Base path | Purpose |
| --- | --- | --- |
| Admin | `/admin-api/` | Admin authentication and crop/master-data management |
| Farmer | `/farmer-api/` | Farmer accounts, stock, listings, metadata, and price predictions |
| Wholesaler | `/wholesaler-api/` | Wholesaler accounts, inventory, orders, and bidding |
| API schema | `/api/schema/` | OpenAPI schema |
| Swagger UI | `/api/doc-with-testing/` | Interactive API documentation |
| ReDoc | `/api/view-only-doc/` | Read-only API documentation |

Selected routes include:

```text
POST /admin-api/api/token/
POST /admin-api/api/token/refresh/

POST /farmer-api/login/
POST /farmer-api/logout/
POST /farmer-api/refresh/
GET  /farmer-api/state/
GET  /farmer-api/district/
GET  /farmer-api/commodity/
GET  /farmer-api/grade/
GET  /farmer-api/variety/
GET  /farmer-api/market/
GET  /farmer-api/price-prediction/

POST /wholesaler-api/login/
POST /wholesaler-api/logout/
POST /wholesaler-api/refresh/
GET  /wholesaler-api/order/

WebSocket /wholesaler-api/ws/bidding/<listing_id>/
```

Most protected endpoints require a JWT access token:

```http
Authorization: Bearer <access-token>
```

Use the Swagger UI or the checked-in `schema.yml` file for the complete request and response definitions.

## Price prediction

The price-prediction module combines:

- Historical mandi prices from data.gov.in
- Weather observations from NASA POWER
- District coordinate data
- Recent price lags and rolling averages
- Recent temperature and rainfall features
- A scikit-learn ensemble pipeline using XGBoost and LightGBM

The inference code expects a trained model at:

```text
ml_models/crop_price_pipeline.pkl
```

If the model needs to be retrained, provide the training dataset expected by `price_predictor/train.py` and run:

```powershell
python -m price_predictor.train
```

The default training path is:

```text
dataset/master_aggriculture_dataset.csv
```

The data.gov.in API key is required when live historical price features are requested. NASA POWER weather data is accessed over the internet at prediction time.

## Testing

Run the Django test suite with:

```powershell
python manage.py test
```

Before testing API flows, make sure MySQL and Redis are running and the `.env` file is configured.

## Production checklist

Before deploying this project:

- Set `DEBUG=False`.
- Replace the development `SECRET_KEY` with a new secret stored outside source control.
- Configure explicit `ALLOWED_HOSTS`.
- Configure production CORS and CSRF origins instead of allowing all origins.
- Use environment variables for database, email, AWS, and API credentials.
- Rotate any credentials that may have been exposed during development.
- Run `python manage.py check --deploy`.
- Use a production ASGI server and configure TLS, process supervision, logging, and Redis persistence.
- Run `collectstatic` and configure media/static storage.
- Review uploaded-file validation and access permissions for user documents and identity images.

## License

This project is licensed under the [MIT License](./LICENSE).
