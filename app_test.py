import unittest
from app import app, users, reservations
from flask import session

class AppTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def tearDown(self):
        reservations.clear()
        with self.app.session_transaction() as sess:
            sess.clear()

    def test_home_redirects_to_login(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.location)

    def test_login_page_loads(self):
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)

    def test_successful_login(self):
        response = self.app.post('/login', data=dict(username='test_user', password='password123'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login successful!', response.data)
        with self.app.session_transaction() as sess:
            self.assertIn('username', sess)

    def test_unsuccessful_login(self):
        response = self.app.post('/login', data=dict(username='wrong_user', password='wrong_password'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)        
        with self.app.session_transaction() as sess:
            flash_message = dict(sess['_flashes']).get('danger')
            self.assertIsNotNone(flash_message, sess['_flashes'])
            self.assertEqual(flash_message, 'Invalid username or password!')
            self.assertNotIn('username', sess)

    def test_logout(self):
        with self.app.session_transaction() as sess:
            sess['username'] = 'test_user'
        response = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.app.session_transaction() as sess:
            flash_message = dict(sess['_flashes']).get('success')
            self.assertIsNotNone(flash_message, sess['_flashes'])
            self.assertEqual(flash_message, 'You have been logged out.')        
            self.assertNotIn('username', sess)

    def test_add_reservation(self):
        with self.app.session_transaction() as sess:
            sess['username'] = 'test_user'
        response = self.app.post('/add_reservation', data=dict(date='2023-11-10', start_time='10:00', duration='60'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Reservation successfully added!', response.data)
        self.assertEqual(len(reservations), 1)

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