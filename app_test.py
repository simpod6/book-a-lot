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

        self.do_login()

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

            return test_user.id
    
    def do_login(self):
        response = self.app.post('/login', data=dict(username='test_user', password='password123'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login successful!', response.data)
        with self.app.session_transaction() as sess:
            self.assertIn('username', sess)

    def test_logout(self):
        with self.app.session_transaction() as sess:
            sess['username'] = 'test_user'
        response = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You have been logged out.', response.data)
        with self.app.session_transaction() as sess:
            self.assertNotIn('username', sess)
    
    def add_reservation(self, reservation_date, reservation_time, reservation_duration):        

        response = self.app.post('/add_reservation', data=dict(
            date=reservation_date,
            start_time=reservation_time,
            duration=reservation_duration
        ), follow_redirects=True)

        return response

    def test_add_reservation(self):

        reservation_date = '2023-03-16'
        reservation_time = '10:00'
        reservation_duration = '60'
        
        test_user_id =  self.create_test_user()
        self.do_login()

        response = self.add_reservation(reservation_date, reservation_time, reservation_duration)        

        self.assertEqual(response.status_code, 200)
        with app.app_context():
            reservation = Reservation.query.filter_by(user_id=test_user_id).first()
            self.assertIsNotNone(reservation)

            start_time = datetime.strptime(f'{reservation_date} {reservation_time}', '%Y-%m-%d %H:%M')
            end_time = start_time + timedelta(minutes=int(reservation_duration))

            self.assertEqual(reservation.start_time, start_time)
            self.assertEqual(reservation.end_time, end_time)



    def test_add_reservation_overlap(self):

        reservation_date = '2023-03-16'
        reservation_time = '10:00'
        reservation_time_2 = '10:30'
        reservation_duration = '60'
        
        test_user_id =  self.create_test_user()
        self.do_login()

        response = self.add_reservation(reservation_date, reservation_time, reservation_duration)        

        self.assertEqual(response.status_code, 200)
        with app.app_context():
            reservation = Reservation.query.filter_by(user_id=test_user_id).first()
            self.assertIsNotNone(reservation)

            start_time = datetime.strptime(f'{reservation_date} {reservation_time}', '%Y-%m-%d %H:%M')
            end_time = start_time + timedelta(minutes=int(reservation_duration))

            self.assertEqual(reservation.start_time, start_time)
            self.assertEqual(reservation.end_time, end_time)
        
        response = self.add_reservation(reservation_date, reservation_time_2, reservation_duration)        
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Reservation overlaps with an existing one!', response.data)
        with app.app_context():
            reservations = Reservation.query.filter_by(user_id=test_user_id)
            self.assertEqual(reservations.count(), 1)

            reservation = reservations.first()
            self.assertIsNotNone(reservation)

            start_time = datetime.strptime(f'{reservation_date} {reservation_time}', '%Y-%m-%d %H:%M')
            end_time = start_time + timedelta(minutes=int(reservation_duration))

            self.assertEqual(reservation.start_time, start_time)
            self.assertEqual(reservation.end_time, end_time)


    def test_cancel_reservation(self):
        reservation_date = '2023-03-16'
        reservation_time = '10:00'        
        reservation_duration = '60'
        reservation = None
        
        test_user_id =  self.create_test_user()
        self.do_login()

        response = self.add_reservation(reservation_date, reservation_time, reservation_duration)        

        self.assertEqual(response.status_code, 200)
        with app.app_context():
            reservation = Reservation.query.filter_by(user_id=test_user_id).first()
            self.assertIsNotNone(reservation)

            start_time = datetime.strptime(f'{reservation_date} {reservation_time}', '%Y-%m-%d %H:%M')
            end_time = start_time + timedelta(minutes=int(reservation_duration))

            self.assertEqual(reservation.start_time, start_time)
            self.assertEqual(reservation.end_time, end_time)


        response = self.app.post('/cancel_reservation', data=dict(reservation_id=reservation.id), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Reservation successfully cancelled!', response.data)
        

        # Check that the reservation was deleted
        with app.app_context():
            reservation = Reservation.query.filter_by(id=reservation.id).first()
            self.assertIsNone(reservation)



if __name__ == '__main__':
    unittest.main()