from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib

app = Flask(__name__)
app.secret_key = 'trek_secret_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trekking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from models import db, User, Trek, Booking

db.init_app(app)

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@trek.com',
            password=hashlib.sha256('admin123'.encode()).hexdigest(),
            role='admin',
            status='active',
            approval_status='approved'
        )
        db.session.add(admin)
        db.session.commit()
        print('Admin seeded  ->  username: admin  |  password: admin123')

    if not User.query.filter_by(username='staff1').first():
        staff = User(
            username='staff1',
            email='staff1@trek.com',
            password=hashlib.sha256('staff123'.encode()).hexdigest(),
            role='staff',
            status='active',
            approval_status='approved',
            phone='9999999999'
        )
        db.session.add(staff)
        db.session.commit()
        print('Staff seeded  ->  username: staff1  |  password: staff123')


def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None


@app.context_processor
def inject_user():
    return dict(current_user=get_current_user)


@app.route('/')
def index():
    user = get_current_user()
    if user:
        if user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        if user.role == 'staff':
            return redirect(url_for('staff_dashboard'))
        return redirect(url_for('user_dashboard'))
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if not user or user.password != hash_password(password):
            flash('Invalid username or password.', 'danger')
            return render_template('login.html')
        if user.status == 'blacklisted':
            flash('Your account is blacklisted. Contact admin.', 'danger')
            return render_template('login.html')
        if user.role == 'staff' and user.approval_status != 'approved':
            flash('Your staff account is pending admin approval.', 'warning')
            return render_template('login.html')
        session['user_id'] = user.id
        flash(f'Welcome, {user.username}!', 'success')
        return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        role     = request.form.get('role', 'user')
        phone    = request.form.get('phone', '').strip()
        if role == 'admin':
            flash('Admin registration is not allowed.', 'danger')
            return render_template('register.html')
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return render_template('register.html')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('register.html')
        approval = 'pending' if role == 'staff' else 'approved'
        new_user = User(username=username, email=email,
                        password=hash_password(password),
                        role=role, status='active',
                        approval_status=approval, phone=phone)
        db.session.add(new_user)
        db.session.commit()
        if role == 'staff':
            flash('Registered! Wait for admin approval.', 'success')
        else:
            flash('Registered successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'success')
    return redirect(url_for('login'))


# ── ADMIN ─────────────────────────────────────────────────────────────────────

@app.route('/admin/dashboard')
def admin_dashboard():
    user = get_current_user()
    if not user or user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    total_treks    = Trek.query.count()
    total_users    = User.query.filter_by(role='user').count()
    total_staff    = User.query.filter_by(role='staff').count()
    total_bookings = Booking.query.count()
    pending_staff  = User.query.filter_by(role='staff', approval_status='pending').count()
    return render_template('admin/dashboard.html',
                           total_treks=total_treks, total_users=total_users,
                           total_staff=total_staff, total_bookings=total_bookings,
                           pending_staff=pending_staff)


@app.route('/admin/treks')
def admin_treks():
    user = get_current_user()
    if not user or user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    q = request.args.get('q', '').strip()
    if q:
        treks = Trek.query.filter(
            Trek.name.ilike(f'%{q}%') | Trek.location.ilike(f'%{q}%')
        ).order_by(Trek.id.desc()).all()
    else:
        treks = Trek.query.order_by(Trek.id.desc()).all()
    return render_template('admin/treks.html', treks=treks, q=q)


@app.route('/admin/treks/add', methods=['GET', 'POST'])
def admin_add_trek():
    user = get_current_user()
    if not user or user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        location    = request.form.get('location', '').strip()
        difficulty  = request.form.get('difficulty', 'Easy')
        duration    = int(request.form.get('duration', 1))
        slots       = int(request.form.get('slots', 10))
        start_str   = request.form.get('start_date', '')
        end_str     = request.form.get('end_date', '')
        description = request.form.get('description', '').strip()
        start_date  = datetime.strptime(start_str, '%Y-%m-%d').date() if start_str else None
        end_date    = datetime.strptime(end_str,   '%Y-%m-%d').date() if end_str   else None
        trek = Trek(name=name, location=location, difficulty=difficulty,
                    duration=duration, available_slots=slots, total_slots=slots,
                    start_date=start_date, end_date=end_date,
                    description=description, status='Open')
        db.session.add(trek)
        db.session.commit()
        flash(f'Trek "{name}" created.', 'success')
        return redirect(url_for('admin_treks'))
    return render_template('admin/trek_form.html', trek=None)


@app.route('/admin/treks/edit/<int:trek_id>', methods=['GET', 'POST'])
def admin_edit_trek(trek_id):
    user = get_current_user()
    if not user or user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    trek = Trek.query.get_or_404(trek_id)
    if request.method == 'POST':
        trek.name       = request.form.get('name', '').strip()
        trek.location   = request.form.get('location', '').strip()
        trek.difficulty = request.form.get('difficulty', 'Easy')
        trek.duration   = int(request.form.get('duration', 1))
        trek.status     = request.form.get('status', trek.status)
        new_slots = int(request.form.get('slots', trek.total_slots))
        booked    = trek.total_slots - trek.available_slots
        trek.total_slots     = new_slots
        trek.available_slots = max(0, new_slots - booked)
        start_str = request.form.get('start_date', '')
        end_str   = request.form.get('end_date', '')
        trek.start_date  = datetime.strptime(start_str, '%Y-%m-%d').date() if start_str else None
        trek.end_date    = datetime.strptime(end_str,   '%Y-%m-%d').date() if end_str   else None
        trek.description = request.form.get('description', '').strip()
        db.session.commit()
        flash('Trek updated.', 'success')
        return redirect(url_for('admin_treks'))
    return render_template('admin/trek_form.html', trek=trek)


@app.route('/admin/treks/delete/<int:trek_id>', methods=['POST'])
def admin_delete_trek(trek_id):
    user = get_current_user()
    if not user or user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    trek = Trek.query.get_or_404(trek_id)
    for b in trek.bookings:
        b.status = 'Cancelled'
    db.session.delete(trek)
    db.session.commit()
    flash('Trek deleted.', 'success')
    return redirect(url_for('admin_treks'))


@app.route('/admin/treks/assign/<int:trek_id>', methods=['GET', 'POST'])
def admin_assign_staff(trek_id):
    user = get_current_user()
    if not user or user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    trek = Trek.query.get_or_404(trek_id)
    staff_list = User.query.filter_by(role='staff', approval_status='approved', status='active').all()
    if request.method == 'POST':
        staff_id = request.form.get('staff_id', '')
        trek.assigned_staff_id = int(staff_id) if staff_id else None
        db.session.commit()
        flash('Staff assignment updated.', 'success')
        return redirect(url_for('admin_treks'))
    return render_template('admin/assign_staff.html', trek=trek, staff_list=staff_list)


@app.route('/admin/staff')
def admin_staff():
    user = get_current_user()
    if not user or user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    q = request.args.get('q', '').strip()
    if q:
        staff_list = User.query.filter_by(role='staff').filter(
            User.username.ilike(f'%{q}%') | User.email.ilike(f'%{q}%')).all()
    else:
        staff_list = User.query.filter_by(role='staff').order_by(User.id.desc()).all()
    return render_template('admin/staff.html', staff_list=staff_list, q=q)


@app.route('/admin/staff/approve/<int:user_id>', methods=['POST'])
def admin_approve_staff(user_id):
    user = get_current_user()
    if not user or user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    staff = User.query.get_or_404(user_id)
    staff.approval_status = 'approved'
    db.session.commit()
    flash(f'{staff.username} approved.', 'success')
    return redirect(url_for('admin_staff'))


@app.route('/admin/staff/blacklist/<int:user_id>', methods=['POST'])
def admin_blacklist_staff(user_id):
    user = get_current_user()
    if not user or user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    staff = User.query.get_or_404(user_id)
    staff.status = 'blacklisted'
    staff.approval_status = 'blacklisted'
    db.session.commit()
    flash(f'{staff.username} blacklisted.', 'warning')
    return redirect(url_for('admin_staff'))


@app.route('/admin/users')
def admin_users():
    user = get_current_user()
    if not user or user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    q = request.args.get('q', '').strip()
    if q:
        users = User.query.filter_by(role='user').filter(
            User.username.ilike(f'%{q}%') | User.email.ilike(f'%{q}%')).all()
    else:
        users = User.query.filter_by(role='user').order_by(User.id.desc()).all()
    return render_template('admin/users.html', users=users, q=q)


@app.route('/admin/users/blacklist/<int:user_id>', methods=['POST'])
def admin_blacklist_user(user_id):
    user = get_current_user()
    if not user or user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    target = User.query.get_or_404(user_id)
    target.status = 'blacklisted'
    db.session.commit()
    flash(f'{target.username} blacklisted.', 'warning')
    return redirect(url_for('admin_users'))


@app.route('/admin/users/activate/<int:user_id>', methods=['POST'])
def admin_activate_user(user_id):
    user = get_current_user()
    if not user or user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    target = User.query.get_or_404(user_id)
    target.status = 'active'
    db.session.commit()
    flash(f'{target.username} activated.', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/bookings')
def admin_bookings():
    user = get_current_user()
    if not user or user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    bookings = Booking.query.order_by(Booking.id.desc()).all()
    return render_template('admin/bookings.html', bookings=bookings)


# ── STAFF ─────────────────────────────────────────────────────────────────────

@app.route('/staff/dashboard')
def staff_dashboard():
    user = get_current_user()
    if not user or user.role != 'staff':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    assigned_treks = Trek.query.filter_by(assigned_staff_id=user.id).all()
    all_treks = Trek.query.order_by(Trek.id.desc()).all()
    return render_template('staff/dashboard.html', assigned_treks=assigned_treks, all_treks=all_treks)


@app.route('/staff/trek/<int:trek_id>')
def staff_trek_detail(trek_id):
    user = get_current_user()
    if not user or user.role != 'staff':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    trek = Trek.query.get_or_404(trek_id)
    if trek.assigned_staff_id != user.id:
        flash('You are not assigned to this trek.', 'danger')
        return redirect(url_for('staff_dashboard'))
    bookings = Booking.query.filter_by(trek_id=trek_id, status='Booked').all()
    return render_template('staff/trek_detail.html', trek=trek, bookings=bookings)


@app.route('/staff/trek/<int:trek_id>/update', methods=['POST'])
def staff_update_trek(trek_id):
    user = get_current_user()
    if not user or user.role != 'staff':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    trek = Trek.query.get_or_404(trek_id)
    if trek.assigned_staff_id != user.id:
        flash('Not your trek.', 'danger')
        return redirect(url_for('staff_dashboard'))
    slots_str  = request.form.get('available_slots', '')
    new_status = request.form.get('status', '')
    if slots_str:
        trek.available_slots = max(0, int(slots_str))
    if new_status:
        trek.status = new_status
    db.session.commit()
    flash('Trek updated.', 'success')
    return redirect(url_for('staff_trek_detail', trek_id=trek_id))


# ── USER ──────────────────────────────────────────────────────────────────────

@app.route('/user/dashboard')
def user_dashboard():
    user = get_current_user()
    if not user or user.role != 'user':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    my_bookings = Booking.query.filter_by(user_id=user.id).order_by(Booking.id.desc()).all()
    open_treks  = Trek.query.filter(Trek.status.in_(['Open', 'Approved'])).count()
    return render_template('user/dashboard.html', my_bookings=my_bookings, open_treks=open_treks)


@app.route('/user/treks')
def user_browse_treks():
    user = get_current_user()
    if not user or user.role != 'user':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    q          = request.args.get('q', '').strip()
    difficulty = request.args.get('difficulty', '').strip()
    location   = request.args.get('location', '').strip()
    query = Trek.query.filter(Trek.status.in_(['Open', 'Approved']))
    if q:
        query = query.filter(Trek.name.ilike(f'%{q}%') | Trek.location.ilike(f'%{q}%'))
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if location:
        query = query.filter(Trek.location.ilike(f'%{location}%'))
    treks = query.order_by(Trek.id.desc()).all()
    return render_template('user/browse_treks.html', treks=treks, q=q,
                           difficulty=difficulty, location=location)


@app.route('/user/treks/book/<int:trek_id>', methods=['POST'])
def user_book_trek(trek_id):
    user = get_current_user()
    if not user or user.role != 'user':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    trek = Trek.query.get_or_404(trek_id)
    if trek.status not in ['Open', 'Approved']:
        flash('This trek is not open for booking.', 'danger')
        return redirect(url_for('user_browse_treks'))
    if trek.available_slots <= 0:
        flash('No slots available.', 'danger')
        return redirect(url_for('user_browse_treks'))
    existing = Booking.query.filter_by(user_id=user.id, trek_id=trek_id, status='Booked').first()
    if existing:
        flash('You have already booked this trek.', 'warning')
        return redirect(url_for('user_browse_treks'))
    booking = Booking(user_id=user.id, trek_id=trek_id, status='Booked')
    trek.available_slots -= 1
    db.session.add(booking)
    db.session.commit()
    flash(f'Successfully booked "{trek.name}"!', 'success')
    return redirect(url_for('user_dashboard'))


@app.route('/user/bookings/cancel/<int:booking_id>', methods=['POST'])
def user_cancel_booking(booking_id):
    user = get_current_user()
    if not user or user.role != 'user':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('user_dashboard'))
    if booking.status == 'Booked':
        booking.status = 'Cancelled'
        booking.trek.available_slots += 1
        db.session.commit()
        flash('Booking cancelled.', 'info')
    else:
        flash('Cannot cancel this booking.', 'warning')
    return redirect(url_for('user_dashboard'))


@app.route('/user/profile', methods=['GET', 'POST'])
def user_profile():
    user = get_current_user()
    if not user or user.role != 'user':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    if request.method == 'POST':
        new_email    = request.form.get('email', '').strip()
        new_phone    = request.form.get('phone', '').strip()
        new_password = request.form.get('password', '')
        if new_email and new_email != user.email:
            taken = User.query.filter_by(email=new_email).first()
            if taken:
                flash('Email already in use.', 'danger')
                return render_template('user/profile.html', user=user)
            user.email = new_email
        if new_phone:
            user.phone = new_phone
        if new_password:
            user.password = hash_password(new_password)
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('user_profile'))
    return render_template('user/profile.html', user=user)


if __name__ == '__main__':
    app.run(debug=True)
