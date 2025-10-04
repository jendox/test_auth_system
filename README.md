# Custom Authentication and Authorization System

A comprehensive backend application implementing a custom authentication and authorization system with FastAPI, PostgreSQL, and JWT tokens.

## 🚀 Features

- **User Management**: Registration, login, profile updates, soft deletion
- **JWT Authentication**: Access/refresh tokens with fingerprint validation
- **Role-Based Access Control (RBAC)**: Flexible permission system
- **Session Management**: Secure session handling with revocation
- **Email Confirmation**: User verification system (stub implementation)
- **Admin API**: Permission management for administrators

## 🛠️ Tech Stack

- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Relational database
- **SQLAlchemy** - ORM with async support
- **Alembic** - Database migrations
- **JWT** - JSON Web Tokens for authentication
- **Docker** - Containerization
- **uv** - Fast Python package manager

## 📥 Installation & Setup

### Clone the Repository
```bash
git clone https://github.com/jendox/test_auth_system.git
cd test_auth_system
```

### Create Environment File
Copy the example environment file and update the values:
```bash
cp example.env .env
```
Edit .env with your configuration.

### Install Dependencies
Using uv (recommended):
```bash
uv sync
```

### Start Database with Docker
```bash
docker-compose up -d
```

Wait for PostgreSQL to be ready (healthcheck will pass).

### Run Database Migrations

Apply the existing migrations (Alembic is already initialized):
```bash
alembic upgrade head
```

###  Populate with Test Data

The test data is automatically loaded with migrations (file a85548e5b3f3_insert_test_data.py).

## 🎯 Usage

### Start the Application
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Access API Documentation
Open your browser and navigate to http://localhost:8000/docs

## 👤 Test Users

The system comes with pre-configured test users:

| Email | Password | Role | Permissions |
| :--- | :--- | :--- | :--- |
| admin@example.com | gfhnfx | Admin | Full access to all resources |
| manager@example.com | Qwerty!234 | Manager | Product and order management |
| user@example.com | Qwerty!234 | User | Basic read operations |

## 🔧 Makefile Commands

The project includes a Makefile for common development tasks:
```bash
# Code quality
make lint    # Check code with linter
make fmt     # Auto-format code

# Development
make run     # Start development server
make up      # Start Docker containers
make down    # Stop Docker containers

# Database
make migrate           # Apply migrations
make makemigrations MESSAGE="Description"  # Create new migration
make downgrade         # Rollback last migration

# Utilities
make token LENGTH=64   # Generate secure token
make list              # Show all available commands
```

## API Endpoints

### 🔐 Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/login` | User login |
| `POST` | `/auth/refresh` | Refresh access token |
| `POST` | `/auth/logout` | User logout |

### 👥 User Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/users` | Register new user |
| `GET` | `/users/me` | Get current user profile |
| `PUT` | `/users/me` | Update profile |
| `DELETE` | `/users/me` | Delete account (soft) |
| `PUT` | `/users/me/password` | Change password |
| `POST` | `/users/confirm-email` | Confirm email address |

### ⚙️ Administration

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/admin/user-permissions/{user_id}` | Get user permissions |
| `PUT` | `/admin/user-permissions/{user_id}` | Set user permissions |
| `DELETE` | `/admin/user-delete/{user_id}` | Delete user |

### 📦 Mock Business Objects

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/mock-api/products` | Get products (requires `product:read`) |
| `PUT` | `/mock-api/products/{id}` | Update product (requires `product:update`) |
| `DELETE` | `/mock-api/products/{id}` | Delete product (requires `product:delete`) |
| `GET` | `/mock-api/orders` | Get orders (requires `order:read`) |
| `GET` | `/mock-api/users` | Get users (requires `user:read`) |

## 🗄️ Database Schema Design

### Access Control System Overview

The system implements a hybrid authorization model that combines **Role-Based Access Control (RBAC)** with **individual user permissions**.

### Core Entities

#### 1. Users (`users`)
```sql
- id (PK) - unique identifier
- email - unique user email
- hashed_password - hashed password (Argon2)
- name - full user name
- is_active - activity flag (soft deletion)
- role_id (FK) - reference to user role
```

#### 2. User Roles (user_roles)
```sql
- id (PK) - unique role identifier
- name - role name (admin, manager, user)
- description - role description
```
#### 3. Resource Types (resource_types)
```sql
- id (PK) - unique identifier
- name - resource type (user, product, order, category)
- description - resource type description
```
#### 4. Permissions (permissions)
```sql
- id (PK) - unique identifier
- name - permission name (user_create, product_read, etc.)
- description - permission description
- resource_type_id (FK) - resource type
- action - action (create, read, update, delete, manage)
```
#### 5. Role-Permission Mapping (role_permissions)
```sql
- role_id (FK) - reference to role
- permission_id (FK) - reference to permission
- composite primary key (role_id, permission_id)
```
#### 6. User Permissions (user_permissions)
```sql
- user_id (FK) - reference to user
- permission_id (FK) - reference to permission
- granted - permission grant flag (true/false)
- granted_by - who granted the permission
- composite primary key (user_id, permission_id)
```
#### 7. User Sessions (user_sessions)
```sql
- id (PK, UUID) - unique session identifier
- user_id (FK) - reference to user
- is_revoked - session revocation flag
- expires_at - session expiration timestamp
```
#### 8. Refresh Tokens (refresh_tokens)
```sql
- session_id (FK) - reference to session
- token_hash - refresh token hash (SHA-256)
- expires_at - token expiration timestamp
- is_revoked - token revocation flag
```
### System Principles

#### Basic Permissions
Basic permissions are determined by the user's role
#### Individual Permissions
Individual permissions can override role-based permissions:
- If permission `granted = true` - added to role permissions
- If permission `granted = false` - overrides role permission
#### Authentication Management
Sessions ensure secure authentication management

Refresh tokens enable secure access token renewal
