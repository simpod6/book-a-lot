from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
import json


load_dotenv()

APP_SECRET_KEY = os.getenv("APP_SECRET_KEY")
PGHOST = os.getenv("PGHOST")
PGUSER = os.getenv("PGUSER")
PGDATABASE = os.getenv("PGDATABASE")
PGPASSWORD = os.getenv("PGPASSWORD")
LANGUAGE = os.getenv("LANGUAGE")
REGISTER_ENABLED = os.getenv("REGISTER_ENABLED", "false")


app = Flask(__name__)
app.secret_key = APP_SECRET_KEY

# Determine the schema based on the environment
schema = 'unit_tests' if os.getenv('FLASK_ENV') == 'testing' else 'runtime'

# SQLAlchemy Configuration for PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@{PGHOST}/{PGDATABASE}'
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

def load_language():
    with open(f'{LANGUAGE}.json', encoding='utf-8') as f:
        return json.load(f)

@app.route('/')
def home():    
    db.create_all()
    if 'username' in session:
        return redirect(url_for('index'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():    
    strings = load_language()

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter(db.func.lower(User.username) == db.func.lower(username)).first()

        if user and check_password_hash(user.password, password):
            session['username'] = username
            session['user_id'] = user.id
            flash(strings['login_successful'], 'success')
            return redirect(url_for('index'))
        
        flash(strings['invalid_username_or_password'], 'danger')        
    return render_template('login.html', strings=strings)

@app.route('/logout')
def logout():    
    strings = load_language()

    session.pop('username', None)
    session.pop('user_id', None)
    flash(strings['you_have_been_logged_out'], 'success')
    return redirect(url_for('login'))

@app.route('/index')
def index():    
    strings = load_language()

    if 'username' not in session:
        flash(strings['please_log_in_to_access_the_system'], 'danger')
        return redirect(url_for('login'))
    
    # Delete past reservations older than 1 week
    one_week_ago = datetime.now() - timedelta(weeks=1)
    past_reservations = Reservation.query.filter(Reservation.end_time < one_week_ago).all()
    for reservation in past_reservations:
        db.session.delete(reservation)
    db.session.commit()
    
     # Fetch all reservations for the calendar
    reservations = Reservation.query.join(User).all()

    # Fetch reservations for the logged-in user (to cancel)
    user_reservations = Reservation.query.filter_by(user_id=session['user_id']).all()

    # Pass both sets of reservations to the template
    return render_template('index.html', 
                           reservations=reservations, 
                           user_reservations=user_reservations,
                           username=session['username'],
                           strings=strings)

@app.route('/api/reservations')
def get_reservations():
    strings = load_language()

    if 'username' not in session:
        flash(strings['you_must_be_logged_in_to_view_reservations'], 'danger')
        return redirect(url_for('login'))
    
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
    strings = load_language()

    # Ensure the user is logged in
    if 'username' not in session:
        flash(strings['you_must_be_logged_in_to_make_a_reservation'], 'danger')
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
        flash(strings['reservation_overlaps_with_an_existing_one'], 'danger')
        return redirect(url_for('index'))
    
    # Add the reservation
    reservation = Reservation(
        user_id=session['user_id'],
        start_time=start_time,
        end_time=end_time
    )
    db.session.add(reservation)
    db.session.commit()

    flash(strings['reservation_successfully_added'], 'success')
    return redirect(url_for('index'))


@app.route('/cancel_reservation', methods=['POST'])
def cancel_reservation():    
    strings = load_language()

    # Ensure the user is logged in
    if 'username' not in session:
        flash(strings['you_must_be_logged_in_to_cancel_a_reservation'], 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']


    reservation_id = request.form.get('reservation_id')

    reservation = Reservation.query.filter_by(id=reservation_id, user_id=user_id).first()
    
    
    if reservation:
        db.session.delete(reservation)
        db.session.commit()
        flash(strings['reservation_successfully_cancelled'], 'success')
    else:
        flash(strings['reservation_not_found_or_not_authorized'], 'danger')

    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():    
    strings = load_language()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash(strings['passwords_do_not_match'], 'danger')
            return redirect(url_for('register'))
        
        if not username.isalnum():
            flash(strings['username_must_contain_only_alphanumeric_characters'], 'danger')
            return redirect(url_for('register'))
        
        existing_user = User.query.filter(db.func.lower(User.username) == db.func.lower(username)).first()        
        if existing_user:
            flash(strings['username_already_exists'], 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        user = User(username=db.func.lower(username), password=hashed_password)
        db.session.add(user)
        db.session.commit()

        flash(strings['registration_successful_please_log_in'], 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', strings=strings, register_enabled=REGISTER_ENABLED)




if __name__ == '__main__':   
    #app.run(debug=True)
    app.run()
