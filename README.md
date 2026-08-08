# Trekking Management Application

A web application built with Flask, SQLAlchemy, Jinja2, HTML and CSS for managing trekking activities involving Admins, Trek Staff, and Users (Trekkers).

## Student Details
- **Name:** A.V Sri Vathsava
- **Project:** Trekking Management Application

---

## Features

### Admin
- Add, edit, delete treks
- Approve or blacklist staff
- Assign staff to treks
- View all users, staff, bookings
- Search treks, staff, users

### Trek Staff
- View assigned treks
- Update trek status (Open / Closed / Completed)
- Update available slots
- View registered participants

### User (Trekker)
- Register and login
- Browse and search open treks
- Filter by difficulty and location
- Book treks (overbooking prevented)
- Cancel bookings
- View trekking history
- Edit profile

---

## Tech Stack

| Technology | Usage |
|------------|-------|
| Python / Flask | Backend web framework |
| SQLAlchemy | ORM for database |
| SQLite | Database |
| Jinja2 | HTML templating |
| HTML + CSS | Frontend |

---

## How to Run

**1. Install dependencies:**
```
pip install flask flask-sqlalchemy
```

**2. Run the app:**
```
python app.py
```

**3. Open browser:**
```
http://127.0.0.1:5000
```

---

## Default Login Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Staff | staff1 | staff123 |

Register as a new User from the Register page.

---

## Project Structure

```
trekking_app/
├── app.py                  # Flask app and all routes
├── models.py               # SQLAlchemy models
├── static/
│   └── css/
│       └── style.css
└── templates/
    ├── base.html
    ├── index.html
    ├── login.html
    ├── register.html
    ├── admin/
    │   ├── dashboard.html
    │   ├── treks.html
    │   ├── trek_form.html
    │   ├── staff.html
    │   ├── users.html
    │   ├── bookings.html
    │   └── assign_staff.html
    ├── staff/
    │   ├── dashboard.html
    │   └── trek_detail.html
    └── user/
        ├── dashboard.html
        ├── browse_treks.html
        └── profile.html
```

---

## Database Models

- **User** — id, username, email, password, role, status, approval_status, phone
- **Trek** — id, name, location, difficulty, duration, slots, status, dates, assigned_staff_id
- **Booking** — id, user_id, trek_id, booking_date, status
