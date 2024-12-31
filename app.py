from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import uuid
import config
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = config.APP_SECRET_KEY

# Determine the schema based on the environment
schema = 'unit_tests' if os.getenv('FLASK_ENV') == 'testing' else 'runtime'

# SQLAlchemy Configuration for PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql+psycopg2://{config.PGUSER}:{config.PGPASSWORD}@{config.PGHOST}/{config.PGDATABASE}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'execution_options': {
        'schema_translate_map': {None: schema}
    }
}

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    user = db.relationship('User', backref='reservations')


# In-memory databases
users = {
    "test_user": "password123",  # username: password
    "Simone": "simone",  # username: password
    "Cri": "cri",  # username: password
}
reservations = []

@app.route('/')
def home():    
    # db.create_all()
    if 'username' in session:
        return redirect(url_for('index'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['username'] = username
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        
        flash('Invalid username or password!', 'danger')        
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/index')
def index():
    if 'username' not in session:
        flash('Please log in to access the system.', 'danger')
        return redirect(url_for('login'))
    
     # Fetch all reservations for the calendar
    reservations = Reservation.query.join(User).all()

    # Fetch reservations for the logged-in user (to cancel)
    user_reservations = Reservation.query.filter_by(user_id=session['user_id']).all()

    # Pass both sets of reservations to the template
    return render_template('index.html', 
                           reservations=reservations, 
                           user_reservations=user_reservations)

@app.route('/api/reservations')
def get_reservations():
    reservations = Reservation.query.join(User).all()
    return jsonify([
        {
            'title': res.user.username,
            'start': res.start_time.isoformat(),
            'end': res.end_time.isoformat()
        }
        for res in reservations
    ])


@app.route('/add_reservation', methods=['POST'])
def add_reservation():
    # Ensure the user is logged in
    if 'username' not in session:
        flash('You must be logged in to make a reservation.', 'danger')
        return redirect(url_for('login'))

    # Fetch data from the form
    date = request.form['date']
    start_time_str = request.form['start_time']
    duration = int(request.form['duration'])

    # Calculate start and end times
    start_time = datetime.strptime(f"{date} {start_time_str}", "%Y-%m-%d %H:%M")
    end_time = start_time + timedelta(minutes=duration)

    # Check for overlapping reservations
    overlapping = Reservation.query.filter(
        Reservation.start_time < end_time,
        Reservation.end_time > start_time
    ).first()

    if overlapping:
        flash('Reservation overlaps with an existing one!', 'danger')
        return redirect(url_for('index'))
    
    # Add the reservation
    reservation = Reservation(
        user_id=session['user_id'],
        start_time=start_time,
        end_time=end_time
    )
    db.session.add(reservation)
    db.session.commit()

    flash('Reservation successfully added!', 'success')
    return redirect(url_for('index'))


@app.route('/cancel_reservation', methods=['GET', 'POST'])
def cancel_reservation():
    # Ensure the user is logged in
    if 'username' not in session:
        flash('You must be logged in to cancel a reservation.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']

    if request.method == 'POST':
        reservation_id = request.form.get('reservation_id')

        reservation = Reservation.query.filter_by(id=reservation_id, user_id=user_id).first()
        
        
        if reservation:
            db.session.delete(reservation)
            db.session.commit()
            flash('Reservation successfully cancelled!', 'success')
        else:
            flash('Reservation not found or not authorized.', 'danger')

        return redirect(url_for('index'))

    user_reservations = Reservation.query.filter_by(user_id=user_id).all()
    formatted_reservations = [
        {
            'id': r.id,
            'display': f"{r.start_time.strftime('%Y-%m-%d %H:%M')} to {r.end_time.strftime('%H:%M')}"
        }
        for r in user_reservations
    ]
    
    return render_template('cancel_reservation.html', reservations=user_reservations)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')




if __name__ == '__main__':   
    #app.run(debug=True)
    app.run()
