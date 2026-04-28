# Aeromiles

A Django web application.

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/inoperatingsystem/aeromiles.git
cd your-repo
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply migrations

```bash
python manage.py migrate
```

### 5. Run the development server

```bash
python manage.py runserver
```

The app will be available at `http://127.0.0.1:8000`.


## Project Structure

```
.
├── manage.py
├── requirements.txt
├── .env
├── config/                 # Project settings and URLs
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── apps/                   # Django apps live here
```

## Contributing

1. Create a feature branch (`git checkout -b feature/your-feature`)
2. Commit your changes (`git commit -m 'Add your feature'`)
3. Push to the branch (`git push origin feature/your-feature`)
4. Open a pull request
