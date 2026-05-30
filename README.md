# spam-detection-server

# Phone Number Verification and Spam Detection API

A REST API for a mobile app that allows users to identify spam calls and search for people by phone number or name.

## Features

- User registration and authentication
- Contact management
- Spam reporting system
- Search functionality by name or phone number
- Privacy-aware contact information display

## Technologies Used

- Django (Python web framework)
- Django REST Framework (for building REST APIs)
- PostgreSQL (relational database)
- JWT (JSON Web Tokens for authentication)

## Installation

### Prerequisites

- Python 3.8+
- PostgreSQL
- pip (Python package manager)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/phone-spam-api.git
   cd phone-spam-api
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
4. Set up environment variables:
   ```bash
   SECRET_KEY=your-django-secret-key
    DB_NAME=your_db_name
    DB_USER=your_db_user
    DB_PASSWORD=your_db_password
    DB_HOST=localhost
    DB_PORT=5432
5.  Run database migrations:
    ```bash
    python manage.py migrate
6.  Populate the database with sample data:
    ```bash
    python manage.py populate_db
7.  Run the development server:
    ```bash
    python manage.py runserver
8.  API Endpoints
   ## API Endpoints

### Authentication

| Endpoint | Method | Description | Request Body | Response | Status Codes |
|----------|--------|-------------|--------------|----------|--------------|
| `/api/auth/register/` | POST | Register a new user | `{name, phone_number, password, [email]}` | User details + tokens | 201, 400 |
| `/api/auth/login/` | POST | Authenticate user | `{phone_number, password}` | Access + refresh tokens | 200, 401 |
| `/api/auth/token/refresh/` | POST | Refresh access token | `{refresh_token}` | New access token | 200, 401 |

### User Profile

| Endpoint | Method | Description | Parameters | Response | Status Codes |
|----------|--------|-------------|------------|----------|--------------|
| `/api/user/` | GET | Get current user profile | - | User details | 200, 401 |
| `/api/user/` | PUT | Update user profile | `{[name], [email]}` | Updated user details | 200, 400, 401 |

### Contacts Management

| Endpoint | Method | Description | Parameters | Response | Status Codes |
|----------|--------|-------------|------------|----------|--------------|
| `/api/contacts/` | GET | List all contacts | `?page=1&limit=20` | Paginated contacts list | 200, 401 |
| `/api/contacts/` | POST | Add new contact | `{name, phone_number, [email]}` | Created contact | 201, 400, 401 |
| `/api/contacts/{id}/` | GET | Get contact details | UUID in path | Contact details | 200, 404, 401 |
| `/api/contacts/{id}/` | PUT | Update contact | UUID in path + contact data | Updated contact | 200, 400, 401, 404 |
| `/api/contacts/{id}/` | DELETE | Delete contact | UUID in path | - | 204, 401, 404 |

### Spam Reporting

| Endpoint | Method | Description | Parameters | Response | Status Codes |
|----------|--------|-------------|------------|----------|--------------|
| `/api/spam/` | POST | Report spam number | `{phone_number, [reason]}` | Spam report details | 201, 400, 401 |
| `/api/spam/{phone_number}/` | GET | Check spam status | Phone number in path | Spam report stats | 200, 401 |

### Search

| Endpoint | Method | Description | Query Parameters | Response | Status Codes |
|----------|--------|-------------|------------------|----------|--------------|
| `/api/search/` | GET | Search by name | `name=<query>&limit=10` | Search results | 200, 401 |
| `/api/search/` | GET | Search by phone | `phone=<number>` | Search results | 200, 401 |

## Detailed Endpoint Specifications

### User Registration (`POST /api/auth/register/`)
**Request:**
```json
{
    "name": "John Doe",
    "phone_number": "+919876543210",
    "password": "SecurePass123!",
    "email": "john@example.com"
}
```
# Production Considerations
## While this is a development implementation, production-ready features include:
- JWT authentication
- Password hashing
- Input validation
- Rate limiting (to be implemented)
- Proper error handling
- Database indexing for performance

# Assumptions
- Phone contacts are automatically imported (implementation not required)
- Phone numbers are validated to be in E.164 format
- All requests require authentication except registration and login-
- Email is only visible to contacts of registered users

# Future Enhancements
## Implement rate limiting
- Add API documentation with Swagger/OpenAPI
- Implement caching for frequent searches
- Add phone number validation service integration
- Implement bulk contact import
- Add admin dashboard for spam management
    

# This README provides:
- 1. Clear installation instructions
- 2. API endpoint documentation
- 3. Production considerations
- 4. Future enhancement ideas

