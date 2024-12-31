import unittest

from flask import session
import os
from werkzeug.security import generate_password_hash

os.environ['FLASK_ENV'] = 'testing'

from app import app, db, User, Reservation
from datetime import datetime, timedelta


class AppTestCase(unittest.TestCase):

    def setUp(self):
        os.environ['FLASK_ENV'] = 'testing'
        self.app = app.test_client()
        self.app.testing = True

        # Create the database schema
        with app.app_context():
            db.create_all()

    def tearDown(self):
        # Drop the database schema
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_home_redirects_to_login(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.location)

    def test_login_page_loads(self):
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)

    def test_successful_login(self):
        # Add a test user to the database
        self.create_test_user()

        response = self.app.post('/login', data=dict(username='test_user', password='password123'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login successful!', response.data)
        with self.app.session_transaction() as sess:
            self.assertIn('username', sess)

    def test_unsuccessful_login(self):
        self.create_test_user()

        response = self.app.post('/login', data=dict(username='wrong_user', password='wrong_password'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid username or password', response.data)

    def create_test_user(self):
        with app.app_context():
            test_user = User(username='test_user', password=generate_password_hash('password123'))
            db.session.add(test_user)
            db.session.commit()

    def test_logout(self):
        with self.app.session_transaction() as sess:
            sess['username'] = 'test_user'
        response = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You have been logged out.', response.data)
        with self.app.session_transaction() as sess:
            self.assertNotIn('username', sess)
        

    def test_add_reservation(self):
        self.create_test_user()

        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=2)

        response = self.app.post('/add_reservation', data=dict(
            user_id=test_user.id,
            start_time=start_time,
            end_time=end_time
        ), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        reservation = Reservation.query.filter_by(user_id=test_user.id).first()
        self.assertIsNotNone(reservation)
        self.assertEqual(reservation.start_time, start_time)

    def test_add_reservation_overlap(self):
        with self.app.session_transaction() as sess:
            sess['username'] = 'test_user'
        reservations.append({
            'id': '1',
            'date': '2023-11-10',
            'start_time': '2023-11-10 10:00',
            'end_time': '2023-11-10 11:00',
            'user': 'test_user',
            'display': '2023-11-10 10:00–11:00 (60 min)'
        })
        response = self.app.post('/add_reservation', data=dict(date='2023-11-10', start_time='10:30', duration='60'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Reservation overlaps with an existing one!', response.data)
        self.assertEqual(len(reservations), 1)

    def test_cancel_reservation(self):
        with self.app.session_transaction() as sess:
            sess['username'] = 'test_user'
        
        reservations.append({
            'id': '1',
            'date': '2023-11-10',
            'start_time': '2023-11-10 10:00',
            'end_time': '2023-11-10 11:00',
            'user': 'test_user',
            'display': '2023-11-10 10:00–11:00 (60 min)'
        })
        response = self.app.post('/cancel_reservation', data=dict(reservation_id='1'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Reservation successfully cancelled!', response.data)
        self.assertEqual(len(reservations), 0)

if __name__ == '__main__':
    unittest.main()