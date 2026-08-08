from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    id               = db.Column(db.Integer, primary_key=True)
    username         = db.Column(db.String(80), unique=True, nullable=False)
    email            = db.Column(db.String(120), unique=True, nullable=False)
    password         = db.Column(db.String(200), nullable=False)
    role             = db.Column(db.String(20), nullable=False, default='user')   # admin / staff / user
    status           = db.Column(db.String(20), nullable=False, default='active') # active / blacklisted
    approval_status  = db.Column(db.String(20), nullable=True, default='pending') # pending / approved / blacklisted
    phone            = db.Column(db.String(20), nullable=True)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)

    # one user -> many bookings
    bookings = db.relationship('Booking', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username} role={self.role}>'


class Trek(db.Model):
    __tablename__ = 'treks'

    id              = db.Column(db.Integer, primary_key=True)
    name            = db.Column(db.String(150), nullable=False)
    location        = db.Column(db.String(150), nullable=False)
    difficulty      = db.Column(db.String(20), nullable=False)          # Easy / Moderate / Hard
    duration        = db.Column(db.Integer, nullable=False)             # days
    available_slots = db.Column(db.Integer, nullable=False, default=10)
    total_slots     = db.Column(db.Integer, nullable=False, default=10)
    status          = db.Column(db.String(20), nullable=False, default='Approved')  # Approved / Open / Closed / Completed
    start_date      = db.Column(db.Date, nullable=True)
    end_date        = db.Column(db.Date, nullable=True)
    description     = db.Column(db.Text, nullable=True)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    # FK to users table (assigned staff)
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    assigned_staff    = db.relationship('User', backref='assigned_treks', foreign_keys=[assigned_staff_id])

    # one trek -> many bookings
    bookings = db.relationship('Booking', backref='trek', lazy=True)

    def __repr__(self):
        return f'<Trek {self.name} status={self.status}>'


class Booking(db.Model):
    __tablename__ = 'bookings'

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    trek_id      = db.Column(db.Integer, db.ForeignKey('treks.id'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status       = db.Column(db.String(20), nullable=False, default='Booked')  # Booked / Cancelled / Completed

    def __repr__(self):
        return f'<Booking id={self.id} user={self.user_id} trek={self.trek_id} status={self.status}>'
