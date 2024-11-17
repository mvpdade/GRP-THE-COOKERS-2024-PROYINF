from flask_login import UserMixin
from . import db

class Usuario(db.Model,UserMixin):
    __tablename__ = 'usuarios'
    u_id = db.Column(db.Integer, primary_key=True)
    password_hash = db.Column(db.String, nullable=False)
    mail = db.Column(db.String, unique=True, nullable=False)
    name = db.Column(db.String, nullable=False)

    def get_id(self):
        return str(self.u_id)

class Imagen(db.Model):
    __tablename__ = 'imagenes'
    img_id = db.Column(db.Integer, primary_key=True)
    u_id = db.Column(db.Integer, db.ForeignKey('usuarios.u_id'), nullable=False)
    url = db.Column(db.String, nullable=False)
    upload_date = db.Column(db.DateTime, nullable=False)
