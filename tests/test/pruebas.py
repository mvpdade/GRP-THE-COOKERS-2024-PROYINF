import unittest
from  app.main import create_app
from app.models import db, Usuario
from werkzeug.security import generate_password_hash

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:bolt123@localhost:5432/cookersdb'
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

            hashed_password = generate_password_hash('password123')
            user = Usuario(name="Test User", mail="test@mail.com", password_hash=hashed_password)
            db.session.add(user)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_register_success(self):
        response = self.client.post('/register', data={
            'name': 'Nuevo Usuario',
            'mail': 'nuevo@mail.com',
            'password': 'contraseña123'
        }, follow_redirects=True)
        
        self.assertIn('Registro exitoso! Ahora puedes iniciar sesión.'.encode('utf-8'), response.data)
        with self.app.app_context():
            user = Usuario.query.filter_by(mail='nuevo@mail.com').first()
            self.assertIsNotNone(user)

    def test_register_existing_email(self):
        response = self.client.post('/register', data={
            'name': 'Test User',
            'mail': 'test@mail.com',
            'password': 'nuevacontraseña'
        }, follow_redirects=True)
        
        self.assertIn('El correo ya está registrado'.encode('utf-8'), response.data)

    def test_login_success(self):
        response = self.client.post('/login', data={
            'mail': 'test@mail.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        self.assertIn('Hola, Test User! Estás en el panel de control.'.encode('utf-8'), response.data)

    def test_login_wrong_password(self):
        response = self.client.post('/login', data={
            'mail': 'test@mail.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        self.assertIn('Correo o contraseña incorrectos'.encode('utf-8'), response.data)

if __name__ == '__main__':
    unittest.main(verbosity=2)