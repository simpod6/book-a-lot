from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime, timedelta
import time
import uuid

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
    return jsonify([
        {
            'title': reservation['user'],
            'start': reservation['start_time'],
            'end': reservation['end_time']
        }
        for reservation in reservations
    ])



@app.route('/add_reservation', methods=['POST'])
def add_reservation():
    # Ensure the user is logged in
    if 'username' not in session:
        flash('You must be logged in to make a reservation.', 'danger')
        return redirect(url_for('login'))

    # Fetch data from the form
    date = request.form['date']
    start_time = request.form['start_time']
    duration = int(request.form['duration'])

    # Calculate start and end times
    start_datetime = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
    end_datetime = start_datetime + timedelta(minutes=duration)

    # Check for overlapping reservations
    for reservation in reservations:
        if reservation['date'] == date:
            existing_start = datetime.strptime(reservation['start_time'], "%Y-%m-%d %H:%M")
            existing_end = datetime.strptime(reservation['end_time'], "%Y-%m-%d %H:%M")
            if start_datetime < existing_end and end_datetime > existing_start:
                flash('Reservation overlaps with an existing one!', 'danger')
                return redirect(url_for('index'))

    duration = int((end_datetime - start_datetime).total_seconds() // 60)
     # Add reservation to the list with a unique ID
    reservations.append({
        'id': str(uuid.uuid4()),  # Generate a unique ID for the reservation
        'date': date,
        'start_time': start_datetime.strftime("%Y-%m-%d %H:%M"),
        'end_time': end_datetime.strftime("%Y-%m-%d %H:%M"),
        'user': session['username'],
        'display': f"{date} {start_datetime.strftime('%H:%M')}–{end_datetime.strftime('%H:%M')} ({duration} min)"
    })

    flash('Reservation successfully added!', 'success')
    return redirect(url_for('index'))


@app.route('/cancel_reservation', methods=['GET', 'POST'])
def cancel_reservation():
    # Ensure the user is logged in
    if 'username' not in session:
        flash('You must be logged in to cancel a reservation.', 'danger')
        return redirect(url_for('login'))

    username = session['username']

    if request.method == 'POST':
        reservation_id = request.form.get('reservation_id')
        
        # Remove the reservation by ID
        reservations[:] = [r for r in reservations if r['id'] != reservation_id]
        
        flash('Reservation successfully cancelled!', 'success')
        return redirect(url_for('index'))

    # Filter and format reservations for the logged-in user
    user_reservations = []
    for r in reservations:
        if r['user'] == username:
            start_time = datetime.strptime(r['start_time'], "%Y-%m-%d %H:%M")
            end_time = datetime.strptime(r['end_time'], "%Y-%m-%d %H:%M")
            duration = int((end_time - start_time).total_seconds() // 60)
            user_reservations.append({
                'id': r['id'],
                'display': f"{r['date']} {start_time.strftime('%H:%M')}–{end_time.strftime('%H:%M')} ({duration} min)"
            })

    return render_template('cancel_reservation.html', reservations=user_reservations)



if __name__ == '__main__':
    #app.run(debug=True)
    app.run()

