import unittest

from flask import session
import os
from werkzeug.security import generate_password_hash

os.environ['FLASK_ENV'] = 'testing'

from app import app, db, User, Reservation
from datetime import datetime, timedelta
import json
from bs4 import BeautifulSoup as BS

LANGUAGE = os.getenv("LANGUAGE")


class AppTestCase(unittest.TestCase):

    def setUp(self):
        os.environ['FLASK_ENV'] = 'testing'
        self.app = app.test_client()
        self.app.testing = True

        self.strings = self.load_language()        

        # Create the database schema
        with app.app_context():
            db.create_all()

    def tearDown(self):
        # Drop the database schema
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def load_language(self):
        with open(f'{LANGUAGE}.json', encoding='utf-8') as f:
            return json.load(f)

    def test_home_redirects_to_login(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.location)
    
    def test_home_redirects_to_index(self):
        with self.app.session_transaction() as sess:
            sess['username'] = 'testuser'
        response = self.app.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/index', response.location)

    def test_login_page_loads(self):
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)

    def test_successful_login(self):
        # Add a test user to the database
        self.create_test_user()

        self.do_login()

    def test_successful_login_with_different_case_username(self):        
        self.create_test_user(username='testuser', password='password123')
        self.do_login(username='TestUser', password='password123')        


    def test_unsuccessful_login(self):
        self.create_test_user()

        response = self.app.post('/login', data=dict(username='wrong_user', password='wrong_password'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(bytes(self.strings['invalid_username_or_password'],'utf-8'), response.data)

    def create_test_user(self, username='testuser', password='password123'):
        with app.app_context():
            test_user = User(username=username, password=generate_password_hash(password))
            db.session.add(test_user)
            db.session.commit()

            return test_user.id
    
    def do_login(self, username='testuser', password='password123'):
        response = self.app.post('/login', data=dict(username=username, password=password), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(bytes(self.strings['login_successful'],'utf-8'), response.data)
        with self.app.session_transaction() as sess:
            self.assertIn('username', sess)

    def test_logout(self):
        with self.app.session_transaction() as sess:
            sess['username'] = 'testuser'
        response = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(bytes(self.strings['you_have_been_logged_out'],'utf-8'), response.data)
        with self.app.session_transaction() as sess:
            self.assertNotIn('username', sess)
    
    def test_index_not_logged_in(self):
        response = self.app.get('/index')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.location)
    
    def add_reservation(self, user_id, reservation_date, reservation_time, reservation_duration, skipChecks=False):

        response = self.app.post('/add_reservation', data=dict(
            date=reservation_date,
            start_time=reservation_time,
            duration=reservation_duration
        ), follow_redirects=True)

        if not skipChecks:
            self.assertEqual(response.status_code, 200)
            with app.app_context():
                reservation = Reservation.query.filter_by(user_id=user_id).first()
                self.assertIsNotNone(reservation)

                start_time = datetime.strptime(f'{reservation_date} {reservation_time}', '%Y-%m-%d %H:%M')
                end_time = start_time + timedelta(minutes=int(reservation_duration))

                self.assertEqual(reservation.start_time, start_time)
                self.assertEqual(reservation.end_time, end_time)

        return response

    def test_add_reservation(self):

        reservation_date = datetime.now().strftime('%Y-%m-%d')
        reservation_time = '10:00'
        reservation_duration = '60'
        
        test_user_id =  self.create_test_user()
        self.do_login()

        self.add_reservation(test_user_id, reservation_date, reservation_time, reservation_duration)        


    def test_add_reservation_overlap(self):

        reservation_date = datetime.now().strftime('%Y-%m-%d')
        reservation_time = '10:00'
        reservation_time_2 = '10:30'
        reservation_duration = '60'
        
        test_user_id =  self.create_test_user()
        self.do_login()

        self.add_reservation(test_user_id, reservation_date, reservation_time, reservation_duration)                
        
        response = self.add_reservation(test_user_id, reservation_date, reservation_time_2, reservation_duration, skipChecks=True)        
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(bytes(self.strings['reservation_overlaps_with_an_existing_one'],'utf-8'), response.data)
        with app.app_context():
            reservations = Reservation.query.filter_by(user_id=test_user_id)
            self.assertEqual(reservations.count(), 1)

            reservation = reservations.first()
            self.assertIsNotNone(reservation)

            start_time = datetime.strptime(f'{reservation_date} {reservation_time}', '%Y-%m-%d %H:%M')
            end_time = start_time + timedelta(minutes=int(reservation_duration))

            self.assertEqual(reservation.start_time, start_time)
            self.assertEqual(reservation.end_time, end_time)
    
    def test_add_reservation_overlap_2(self):
        
        reservation_date = datetime.now().strftime('%Y-%m-%d')
        reservation_time = '10:00'
        reservation_time_2 = '09:30'
        reservation_duration = '60'
        
        test_user_id =  self.create_test_user()
        self.do_login()

        self.add_reservation(test_user_id, reservation_date, reservation_time, reservation_duration)                
        
        response = self.add_reservation(test_user_id, reservation_date, reservation_time_2, reservation_duration, skipChecks=True)        
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(bytes(self.strings['reservation_overlaps_with_an_existing_one'],'utf-8'), response.data)
        with app.app_context():
            reservations = Reservation.query.filter_by(user_id=test_user_id)
            self.assertEqual(reservations.count(), 1)

            reservation = reservations.first()
            self.assertIsNotNone(reservation)

            start_time = datetime.strptime(f'{reservation_date} {reservation_time}', '%Y-%m-%d %H:%M')
            end_time = start_time + timedelta(minutes=int(reservation_duration))

            self.assertEqual(reservation.start_time, start_time)
            self.assertEqual(reservation.end_time, end_time)
    
    def test_add_reservation_overlap_identical(self):
        
        reservation_date = datetime.now().strftime('%Y-%m-%d')
        reservation_time = '9:30'
        reservation_duration = '60'
        
        test_user_id =  self.create_test_user()
        self.do_login()

        self.add_reservation(test_user_id, reservation_date, reservation_time, reservation_duration)                
        
        response = self.add_reservation(test_user_id, reservation_date, reservation_time, reservation_duration, skipChecks=True)        
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(bytes(self.strings['reservation_overlaps_with_an_existing_one'],'utf-8'), response.data)
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
        reservation_date = datetime.now().strftime('%Y-%m-%d')
        reservation_time = '10:00'        
        reservation_duration = '60'
        
        
        test_user_id =  self.create_test_user()
        self.do_login()

        self.add_reservation(test_user_id, reservation_date, reservation_time, reservation_duration)

        reservation = None
        with app.app_context():
            reservation = Reservation.query.filter_by(user_id=test_user_id).first()
            self.assertIsNotNone(reservation)

        response = self.app.post('/cancel_reservation', data=dict(reservation_id=reservation.id), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(bytes(self.strings['reservation_successfully_cancelled'],'utf-8'), response.data)
        

        # Check that the reservation was deleted
        with app.app_context():
            reservation = Reservation.query.filter_by(id=reservation.id).first()
            self.assertIsNone(reservation)

    def test_cancel_reservation_wrong_user(self):
        reservation_date = datetime.now().strftime('%Y-%m-%d')
        reservation_time = '10:00'        
        reservation_duration = '60'
        
        
        test_user_id =  self.create_test_user()
        self.do_login()

        self.add_reservation(test_user_id, reservation_date, reservation_time, reservation_duration)

        reservation = None
        with app.app_context():
            reservation = Reservation.query.filter_by(user_id=test_user_id).first()
            self.assertIsNotNone(reservation)

        with app.app_context():
            test_user_2_id = self.create_test_user(username='testuser2', password='password123')
            self.do_login(username='testuser2', password='password123')

            response = self.app.post('/cancel_reservation', data=dict(reservation_id=reservation.id), follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(bytes(self.strings['reservation_not_found_or_not_authorized'],'utf-8'), response.data)
            
            # Check that the reservation was not deleted
            reservation = Reservation.query.filter_by(id=reservation.id).first()
            self.assertIsNotNone(reservation)
    
    def test_cancel_reservation_not_found(self):
        test_user_id =  self.create_test_user()
        self.do_login()

        response = self.app.post('/cancel_reservation', data=dict(reservation_id=1), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(bytes(self.strings['reservation_not_found_or_not_authorized'],'utf-8'), response.data)

    def test_cancel_reservation_not_logged_in(self):
        response = self.app.post('/cancel_reservation', data=dict(reservation_id=1), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(bytes(self.strings['you_must_be_logged_in_to_cancel_a_reservation'],'utf-8'), response.data)

    def test_add_reservation_not_logged_in(self):
        response = self.app.post('/add_reservation', data=dict(
            date=datetime.now().strftime('%Y-%m-%d'),
            start_time='10:00',
            duration='60'
        ), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(bytes(self.strings['you_must_be_logged_in_to_make_a_reservation'],'utf-8'), response.data)
    
    def test_multiple_users_add_reservation(self):
        reservation_date = datetime.now().strftime('%Y-%m-%d')
        reservation_time = '10:00'
        reservation_duration = '60'

        reservation_date_2 = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
    
        
        test_user_id =  self.create_test_user()
        self.do_login()

        self.add_reservation(test_user_id, reservation_date, reservation_time, reservation_duration)        

        with app.app_context():
            test_user_2_id = self.create_test_user(username='testuser2', password='password123')
            self.do_login(username='testuser2', password='password123')

            self.add_reservation(test_user_2_id, reservation_date_2, reservation_time, reservation_duration)        

        with app.app_context():
            reservations = Reservation.query.all()
            self.assertEqual(len(reservations), 2)

            reservation_1 = reservations[0]
            reservation_2 = reservations[1]

            self.assertIsNotNone(reservation_1)
            self.assertIsNotNone(reservation_2)

            start_time = datetime.strptime(f'{reservation_date} {reservation_time}', '%Y-%m-%d %H:%M')
            end_time = start_time + timedelta(minutes=int(reservation_duration))

            self.assertEqual(reservation_1.start_time, start_time)
            self.assertEqual(reservation_1.end_time, end_time)

            self.assertEqual(reservation_1.user_id, test_user_id)

            start_time_2 = datetime.strptime(f'{reservation_date_2} {reservation_time}', '%Y-%m-%d %H:%M')
            end_time_2 = start_time_2 + timedelta(minutes=int(reservation_duration))

            self.assertEqual(reservation_2.start_time, start_time_2)
            self.assertEqual(reservation_2.end_time, end_time_2)

            self.assertEqual(reservation_2.user_id, test_user_2_id)

    def test_multiple_users_cancel_reservation(self):
        reservation_date = datetime.now().strftime('%Y-%m-%d')
        reservation_time = '10:00'
        reservation_duration = '60'

        reservation_date_2 = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
        
        test_user_id =  self.create_test_user()
        self.do_login()

        self.add_reservation(test_user_id, reservation_date, reservation_time, reservation_duration)        

        with app.app_context():
            test_user_2_id = self.create_test_user(username='testuser2', password='password123')
            self.do_login(username='testuser2', password='password123')

            self.add_reservation(test_user_2_id, reservation_date_2, reservation_time, reservation_duration)        

        with app.app_context():
            reservations = Reservation.query.all()
            self.assertEqual(len(reservations), 2)

            reservation_1 = reservations[0]
            reservation_2 = reservations[1]

            self.assertIsNotNone(reservation_1)
            self.assertIsNotNone(reservation_2)

            start_time = datetime.strptime(f'{reservation_date} {reservation_time}', '%Y-%m-%d %H:%M')
            end_time = start_time + timedelta(minutes=int(reservation_duration))

            self.assertEqual(reservation_1.start_time, start_time)
            self.assertEqual(reservation_1.end_time, end_time)

            self.assertEqual(reservation_1.user_id, test_user_id)

            start_time_2 = datetime.strptime(f'{reservation_date_2} {reservation_time}', '%Y-%m-%d %H:%M')
            end_time_2 = start_time_2 + timedelta(minutes=int(reservation_duration))

            self.assertEqual(reservation_2.start_time, start_time_2)
            self.assertEqual(reservation_2.end_time, end_time_2)

            self.assertEqual(reservation_2.user_id, test_user_2_id)

            self.do_login()

            response = self.app.post('/cancel_reservation', data=dict(reservation_id=reservation_1.id), follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(bytes(self.strings['reservation_successfully_cancelled'],'utf-8'), response.data)

            reservations = Reservation.query.all()
            self.assertEqual(len(reservations), 1)

            reservation = reservations[0]
            self.assertEqual(reservation.id, reservation_2.id)
            self.assertEqual(reservation.user_id, reservation_2.user_id)

    def test_multiple_users_cancel_reservation_other_user(self):
        reservation_date = datetime.now().strftime('%Y-%m-%d')
        reservation_time = '10:00'
        reservation_duration = '60'

        reservation_date_2 = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
        
        test_user_id =  self.create_test_user()
        self.do_login()

        self.add_reservation(test_user_id, reservation_date, reservation_time, reservation_duration)        

        with app.app_context():
            test_user_2_id = self.create_test_user(username='testuser2', password='password123')
            self.do_login(username='testuser2', password='password123')

            self.add_reservation(test_user_2_id, reservation_date_2, reservation_time, reservation_duration)        

        with app.app_context():
            reservations = Reservation.query.all()
            self.assertEqual(len(reservations), 2)

            reservation_1 = reservations[0]
            reservation_2 = reservations[1]

            self.assertIsNotNone(reservation_1)
            self.assertIsNotNone(reservation_2)

            start_time = datetime.strptime(f'{reservation_date} {reservation_time}', '%Y-%m-%d %H:%M')
            end_time = start_time + timedelta(minutes=int(reservation_duration))

            self.assertEqual(reservation_1.start_time, start_time)
            self.assertEqual(reservation_1.end_time, end_time)

            self.assertEqual(reservation_1.user_id, test_user_id)

            start_time_2 = datetime.strptime(f'{reservation_date_2} {reservation_time}', '%Y-%m-%d %H:%M')
            end_time_2 = start_time_2 + timedelta(minutes=int(reservation_duration))

            self.assertEqual(reservation_2.start_time, start_time_2)
            self.assertEqual(reservation_2.end_time, end_time_2)

            self.assertEqual(reservation_2.user_id, test_user_2_id)

            self.do_login()

            response = self.app.post('/cancel_reservation', data=dict(reservation_id=reservation_2.id), follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(bytes(self.strings['reservation_not_found_or_not_authorized'],'utf-8'), response.data)

            self.assertEqual(len(reservations), 2)

            reservation_1 = reservations[0]
            reservation_2 = reservations[1]

            self.assertIsNotNone(reservation_1)
            self.assertIsNotNone(reservation_2)

            start_time = datetime.strptime(f'{reservation_date} {reservation_time}', '%Y-%m-%d %H:%M')
            end_time = start_time + timedelta(minutes=int(reservation_duration))

            self.assertEqual(reservation_1.start_time, start_time)
            self.assertEqual(reservation_1.end_time, end_time)

            self.assertEqual(reservation_1.user_id, test_user_id)

            start_time_2 = datetime.strptime(f'{reservation_date_2} {reservation_time}', '%Y-%m-%d %H:%M')
            end_time_2 = start_time_2 + timedelta(minutes=int(reservation_duration))

            self.assertEqual(reservation_2.start_time, start_time_2)
            self.assertEqual(reservation_2.end_time, end_time_2)

            self.assertEqual(reservation_2.user_id, test_user_2_id)
    
    # tests for api/reservations
    def test_reservations_api(self):
        reservation_date = datetime.now().strftime('%Y-%m-%d')
        reservation_time = '10:00'
        reservation_duration = '60'

        reservation_date_2 = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
        
        test_user_id =  self.create_test_user()
        self.do_login()

        self.add_reservation(test_user_id, reservation_date, reservation_time, reservation_duration)        

        with app.app_context():
            test_user_2_id = self.create_test_user(username='testuser2', password='password123')
            self.do_login(username='testuser2', password='password123')

            self.add_reservation(test_user_2_id, reservation_date_2, reservation_time, reservation_duration)        

        response = self.app.get('/api/reservations', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # parse the json response
        reservations = response.get_json()
        self.assertEqual(len(reservations), 2)
        self.assertEqual(reservations[0]['title'], 'testuser')
        self.assertEqual(reservations[1]['title'], 'testuser2')

        start_time_1 = datetime.strptime(f"{reservation_date} {reservation_time}", "%Y-%m-%d %H:%M")
        end_time_1 = start_time_1 + timedelta(minutes=int(reservation_duration))

        start_time_2 = datetime.strptime(f"{reservation_date_2} {reservation_time}", "%Y-%m-%d %H:%M")
        end_time_2 = start_time_2 + timedelta(minutes=int(reservation_duration))

        self.assertEqual(reservations[0]['start'], start_time_1.isoformat())
        self.assertEqual(reservations[1]['start'], start_time_2.isoformat())

        self.assertEqual(reservations[0]['end'], end_time_1.isoformat())
        self.assertEqual(reservations[1]['end'], end_time_2.isoformat())
    
    # tests for api/reservations: test that reservations older than 1 week are not returned
    def test_reservations_api_old_reservations(self):
        reservation_date = (datetime.now() - timedelta(weeks=2)).strftime('%Y-%m-%d')
        reservation_time = '10:00'
        reservation_duration = '60'

        reservation_date_2 = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
    
        
        test_user_id =  self.create_test_user()
        self.do_login()

        self.add_reservation(test_user_id, reservation_date, reservation_time, reservation_duration)        

        with app.app_context():
            test_user_2_id = self.create_test_user(username='testuser2', password='password123')
            self.do_login(username='testuser2', password='password123')

            self.add_reservation(test_user_2_id, reservation_date_2, reservation_time, reservation_duration)        

        response = self.app.get('/api/reservations', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # parse the json response
        reservations = response.get_json()
        self.assertEqual(len(reservations), 1)
        self.assertEqual(reservations[0]['title'], 'testuser2')

        start_time_2 = datetime.strptime(f"{reservation_date_2} {reservation_time}", "%Y-%m-%d %H:%M")
        end_time_2 = start_time_2 + timedelta(minutes=int(reservation_duration))

        self.assertEqual(reservations[0]['start'], start_time_2.isoformat())
        self.assertEqual(reservations[0]['end'], end_time_2.isoformat())
        
    def test_reservations_api_not_logged_in(self):
        response = self.app.get('/api/reservations', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(bytes(self.strings['you_must_be_logged_in_to_view_reservations'],'utf-8'), response.data)
    
    def test_reservations_api_no_reservations(self):
        test_user_id =  self.create_test_user()
        self.do_login()

        response = self.app.get('/api/reservations', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'[]', response.data)
    
    # test /stats page
    def test_stats_page(self):
        reservation_date = datetime.now().strftime('%Y-%m-%d')
        reservation_time = '10:00'
        reservation_duration = '60'

        reservation_date_2 = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
        
        test_user_id =  self.create_test_user()
        self.do_login()

        self.add_reservation(test_user_id, reservation_date, reservation_time, reservation_duration)        

        with app.app_context():
            test_user_2_id = self.create_test_user(username='testuser2', password='password123')
            self.do_login(username='testuser2', password='password123')

            self.add_reservation(test_user_2_id, reservation_date_2, reservation_time, reservation_duration)        

        response = self.app.get('/stats', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Total Reservations: 2', response.data)
        soup = BS(response.data, 'html.parser')
        table = soup.find('table')
        self.assertIsNotNone(table)
        row1 = table.find_all('tr')[1]
        self.assertEqual(row1.find_all('td')[0].text, 'testuser')
        self.assertEqual(row1.find_all('td')[1].text, '0')
        self.assertEqual(row1.find_all('td')[2].text, '1')
        row2 = table.find_all('tr')[2]
        self.assertEqual(row2.find_all('td')[0].text, 'testuser2')
        self.assertEqual(row2.find_all('td')[1].text, '1')
        self.assertEqual(row2.find_all('td')[2].text, '1')
    
    def test_stats_page_not_logged_in(self):
        response = self.app.get('/stats', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(bytes(self.strings['please_log_in_to_access_the_system'],'utf-8'), response.data)

    def test_register_page_loads(self):
        response = self.app.get('/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Register', response.data)
    
    def test_register_user(self):
        response = self.app.post('/register', data=dict(username='testuser', password='password123', confirm_password='password123'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(bytes(self.strings['registration_successful_please_log_in'],'utf-8'), response.data)
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            self.assertIsNotNone(user)
        
        self.do_login()

    def test_register_user_with_numeric_chars(self):
        response = self.app.post('/register', data=dict(username='testuser2', password='password123', confirm_password='password123'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(bytes(self.strings['registration_successful_please_log_in'],'utf-8'), response.data)
        with app.app_context():
            user = User.query.filter_by(username='testuser2').first()
            self.assertIsNotNone(user)
        
        self.do_login(username='testuser2', password='password123')
    
    def test_register_user_with_different_case_username(self):
        response = self.app.post('/register', data=dict(username='TestUser', password='password123', confirm_password='password123'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(bytes(self.strings['registration_successful_please_log_in'],'utf-8'), response.data)
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            self.assertIsNotNone(user)
        
        self.do_login()        
    
    def test_register_user_password_mismatch(self):
        response = self.app.post('/register', data=dict(username='testuser', password='password123', confirm_password='password1234'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(bytes(self.strings['passwords_do_not_match'],'utf-8'), response.data)
    
    def test_register_user_already_exists(self):
        self.create_test_user()
        response = self.app.post('/register', data=dict(username='testuser', password='password123', confirm_password='password123'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(bytes(self.strings['username_already_exists'],'utf-8'), response.data)
    
    def test_register_user_invalid_username(self):
        response = self.app.post('/register', data=dict(username='testuser@abc.com', password='password123', confirm_password='password123'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(bytes(self.strings['username_must_contain_only_alphanumeric_characters'],'utf-8'), response.data)

if __name__ == '__main__':
    unittest.main()