from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime, timedelta
import time

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# In-memory databases
users = {
    "test_user": "password123",  # username: password
    "Simone": "simone",  # username: password
    "Cri": "cri",  # username: password
}
reservations = []

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('index'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in users and users[username] == password:
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        flash('Invalid username or password!', 'danger')        
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/index')
def index():
    if 'username' not in session:
        flash('Please log in to access the system.', 'danger')
        return redirect(url_for('login'))
    return render_template('index.html', reservations=reservations, username=session['username'])

@app.route('/api/reservations')
def get_reservations():
    # Return reservations in a format suitable for FullCalendar
    events = [
        {'title': f"{res['user_name']} ({res['start_time']} - {res['end_time']})",
         'start': res['start_time'], 'end': res['end_time']}
        for res in reservations
    ]
    return jsonify(events)

@app.route('/reserve', methods=['POST'])
def reserve():
    if 'username' not in session:
        flash('Please log in to make a reservation.', 'danger')
        return redirect(url_for('login'))

    user_name = session['username']
    date = request.form.get('date')
    start_time = request.form.get('start_time')
    end_time = request.form.get('end_time')

    if not date or not start_time or not end_time:
        flash('Date, start time, and end time must all be provided!', 'danger')
        return redirect(url_for('index'))

    start_datetime = f"{date} {start_time}:00"
    end_datetime = f"{date} {end_time}:00"

    if start_datetime >= end_datetime:
        flash('End time must be after start time!', 'danger')
        return redirect(url_for('index'))

    # Check for overlap
    for res in reservations:
        if res['start_time'] < end_datetime and res['end_time'] > start_datetime:
            flash('This time slot is already reserved!', 'danger')
            return redirect(url_for('index'))

    reservations.append({'user_name': user_name, 'start_time': start_datetime, 'end_time': end_datetime})
    flash('Reservation successful!', 'success')
    return redirect(url_for('index'))

@app.route('/cancel', methods=['POST'])
def cancel():
    if 'username' not in session:
        flash('Please log in to cancel a reservation.', 'danger')
        return redirect(url_for('login'))

    user_name = session['username']
    start_time = request.form.get('start_time')
    end_time = request.form.get('end_time')

    reservation = next((res for res in reservations if res['user_name'] == user_name and
                        res['start_time'] == start_time and res['end_time'] == end_time), None)
    if reservation:
        reservations.remove(reservation)
        flash('Reservation canceled successfully!', 'success')
    else:
        flash('Reservation not found!', 'danger')

    return redirect(url_for('index'))

if __name__ == '__main__':
    #app.run(debug=True)
    app.run()

