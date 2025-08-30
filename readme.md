# Student Management System


The Student Management System is a web-based application built with pure Django that provides an efficient way to manage students, courses, and enrollments. It allows administrators, teachers, and staff to handle student records, assign courses, track performance, and search/filter data with ease.

This project demonstrates the use of Django’s core features (models, views, templates, and forms) without relying on additional frameworks, making it lightweight, customizable, and easy to extend.
## 🌟 Features

- Student Management: Add, edit, and delete student records with personal information and metadata.

- Course Management: Create and manage courses with unique codes and descriptions.

- Enrollment Management: Assign students to courses and track their performance.

- Search & Filtering: Search students and courses by name, email, course code, or metadata key/value.

- Status Management: Track active/inactive students and courses.

- User Authentication: Secure login system with role-based access (admin, staff, teacher).

- Metadata Support: Flexible key/value metadata for students and courses for extended information.

- Responsive Templates: Clean, easy-to-use UI built with Django templates.

- Audit Fields: Automatic tracking of created and updated timestamps for records.

- Robust Validation: Ensures unique and valid entries for critical fields like email and course codes.
- 
## 🔧 Technology Stack

- **Backend**: Python, Django (pure Django, no additional frameworks)
- **Database**: PostgreSQL 16+
- **Frontend**: Django Templates, HTML, CSS, Bootstrap (for responsive UI)
- **Authentication & Authorization**: Django’s built-in user system with role-based access
- **Version Control:**: GitHub

## 📋 Prerequisites

Before setting up the project, ensure you have the following installed:

- Python 3.12+ 
- PostgreSQL 16+
- Git
- pip
- virtualenv (optional for development)

## 🚀 Getting Started

Follow these steps to set up and run the project locally:

### 1. Clone the Repository

```bash
git clone git@github.com:anish-gc/student-management-system.git
cd student-management-system
```

### 2. Set Up Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements/development.txt
```

### 4. Configure PostgreSQL

Make sure PostgreSQL is installed and running. Create a database for the project:

```bash
# Access PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE student_management_system;

# Exit PostgreSQL
\q
```

### 5. Environment Variables

Create a `.env` file in the project root (You can take sample from .env-sample. Just copy all the contents to .env):

```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=student_management_system   
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=65535
SECRET_KEY  =django-insecure-i!wy@*w#(5ipj$*x8ht7=6k=t_&5y_9x-^zztmk7hze&n#xe_q
DEBUG=True
ALLOWED_HOSTS=localhost



```
### 6. Restore the backup from the file student_management_system.backup using command.After restore, you dont need to run makemigrations. It contains superuser, group, staff, students, instructors, course, enrollments, metadata. Skip step 7, 8, 9  if you follow this step. Replace student_management_system with ur db_name

```bash
pg_restore -h localhost -U postgres -W -d student_management_system student_management_system.backup

```
### 7. Run Migrations(only if u didnot follow step 6)

```bash
python manage.py makemigrations
python manage.py migrate
```

### 8. Create a Superuser(only if u didnot follow step 6)

```bash
python manage.py createsuperuser
```

### 9. Run this base commands sequentially (only if u didnot follow step 6)

```bash
python manage.py create_sample_datas

```

### 10. Run the development Server

```bash
python manage.py runserver
The application should now be accessible at http://localhost:8000.
```


```
## 🗂️ Project Structure

```
```
 accounts
│   ├── admin.py
│   ├── apps.py
│   ├── context_processors.py
│   ├── forms
│   │   ├── group_form.py
│   │   └── staff_form.py
│   ├── __init__.py
│   ├── management
│   │   ├── commands
│   │   └── __init__.py
│   ├── middleware.py
│   ├── migrations
│   │   └── __init__.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views
│       ├── authentication_views.py
│       ├── dashboard_views.py
│       ├── group_views.py
│       ├── staff_views.py
│       └── toggle_views.py
├── core
│   ├── asgi.py
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── logs
│   ├── auth.log
│   └── django.log
├── manage.py
├── readme.md
├── requirements
│   └── development.txt
├── static
│   ├── admin
│   │   ├── css
│   │   ├── images
│   │   ├── js
│   │   └── plugins
│   └── authentication
│       ├── adminlte.css
│       └── adminlte.js
├── students
│   ├── admin.py
│   ├── apps.py
│   ├── forms
│   │   ├── course_form.py
│   │   ├── enrollment_form.py
│   │   ├── instructor_form.py
│   │   ├── metadata_forms.py
│   │   └── student_form.py
│   ├── __init__.py
│   ├── migrations
│   │   └── __init__.py
│   ├── models
│   │   ├── course_model.py
│   │   ├── enrollment_model.py
│   │   ├── __init__.py
│   │   ├── instructor_model.py
│   │   ├── metadata_model.py
│   │   └── student_model.py
│   ├── tests.py
│   ├── urls.py
│   └── views
│       ├── course_views.py
│       ├── enrollment_views.py
│       ├── instructor_views.py
│       ├── metadata_views.py
│       └── student_views.py
├── templates
│   ├── 403.html
│   ├── accounts
│   │   ├── groups
│   │   └── staffs
│   ├── authentication
│   │   └── login.html
│   ├── base.html
│   ├── dashboard.html
│   ├── includes
│   │   ├── content_header_in_form.html
│   │   ├── content_header_in_list.html
│   │   ├── footer.html
│   │   ├── navbar.html
│   │   ├── pagination_partial.html
│   │   ├── preloader.html
│   │   ├── sidebar.html
│   │   └── sweet_alert.html
│   └── students
│       ├── courses
│       ├── enrollments
│       ├── instructors
│       ├── metadata
│       └── students
├── ticket_management_system.backup
├── utilities
│   ├── custom_crud_class.py
│   ├── models.py
│   └── pagination_mixin.py
└── venv


```

