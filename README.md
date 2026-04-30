# Aeromiles

A Django web application.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed and running on your machine.

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/inoperatingsystem/aeromiles.git
cd aeromiles
```

### 2. Set up environment variables

Create a `.env` file in the root directory. You can use this for any Django settings required:

```env
# Example .env file content
POSTGRES_DB=aeromiles_db
POSTGRES_USER=aeromiles_user
POSTGRES_PASSWORD=aeromiles_password
```

### 3. Build and Start the Containers

We use Docker Compose to run the PostgreSQL database and the Django web server together. To build the images and start the containers in the background, run:

```bash
docker-compose up --build -d
```

### 4. Database Setup (Crucial Step)

Since this project relies on a custom database schema (`AEROMILES`), you **must** import the SQL files into the PostgreSQL container before running Django migrations. 

First, import the main schema structure:
```bash
cat dumpsql.sql | docker-compose exec -T db psql -U aeromiles_user -d aeromiles_db
```

Second, populate the database with dummy data:
```bash
cat dummy.sql | docker-compose exec -T db psql -U aeromiles_user -d aeromiles_db
```

Finally, apply Django's built-in migrations (this handles internal tables like user sessions):
```bash
docker-compose exec web python manage.py migrate
```

### 5. Access the Project

The application should now be available at `http://localhost:8000`.

To test the login functionality, you can use any of the pre-inserted dummy accounts. For example:
- **Login as Member:** 
  - Email: `user1@mail.com`
  - Password: `hashedpw1`
- **Login as Staf:** 
  - Email: `user51@mail.com`
  - Password: `hashedpw51`

## Useful Docker Commands

- **Stop the application:**
  ```bash
  docker-compose down
  ```
- **Reset the database entirely (Warning: deletes all data!):**
  ```bash
  docker-compose down -v
  ```
- **View terminal logs:**
  ```bash
  docker-compose logs -f
  ```
- **Run the Django shell:**
  ```bash
  docker-compose exec web python manage.py shell
  ```
- **Access the PostgreSQL shell:**
  ```bash
  docker-compose exec db psql -U <your_username> -d <your_database_name>
  ```

## Project Structure

```
.
├── manage.py
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── .env                    # (You need to create this)
├── config/                 # Project settings and URLs
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── main/                   # Django app
```

## Contributing

1. Create a feature branch (`git checkout -b feat/your-feature`)
2. Commit your changes (`git commit -m 'Add your feature'`)
3. Push to the branch (`git push origin feat/your-feature`)
4. Open a pull request
