from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Usuario, Imagen
import pydicom
import os
import numpy as np
import matplotlib.pyplot as plt
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib
#from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

matplotlib.use('Agg')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:bolt123@localhost:5432/cookersdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = '71067522804f5305cbuenasf618ce50a2df235fd5ab337cb4'

db.init_app(app)

login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    with app.app_context():
        return db.session.get(Usuario, int(user_id))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['mail']
        password = request.form['password']

        with app.app_context():
            user = Usuario.query.filter_by(mail=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('inicio'))
        else:
            flash('Correo o contraseña incorrectos')

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['mail']
        password = request.form['password']

        password_hash = generate_password_hash(password)
        nuevo_usuario = Usuario(name=name, mail=email, password_hash=password_hash)
        
        try:
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash('Registro exitoso! Ahora puedes iniciar sesión.')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            flash('El correo ya está registrado')
            return redirect(url_for('register'))

    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/inicio")
@login_required
def inicio():
    return render_template("inicio.html",user = current_user.name)

def procesar_imagen(ruta):
    ruta = "./imagenes-dicom/" + ruta
    ct_images = os.listdir(ruta)
    slices = [pydicom.read_file(os.path.join(ruta, s), force=True) for s in ct_images]
    slices = sorted(slices, key=lambda x: x.ImagePositionPatient[2])

    pixel_spacing = slices[0].PixelSpacing
    slice_thickness = slices[0].SliceThickness

    axial_aspect_ratio = pixel_spacing[0] / pixel_spacing[1]
    sagital_aspect_ratio = pixel_spacing[1] / slice_thickness
    coronal_aspect_ratio = slice_thickness / pixel_spacing[0]

    img_shape = list(slices[0].pixel_array.shape)
    img_shape.append(len(slices))
    volume3d = np.zeros(img_shape)

    for i, s in enumerate(slices):
        array2D = s.pixel_array
        volume3d[:, :, i] = array2D

    return volume3d, axial_aspect_ratio, sagital_aspect_ratio, coronal_aspect_ratio, img_shape

def generar_imagen(tipo,ruta):
    volume3d, axial_aspect_ratio, sagital_aspect_ratio, coronal_aspect_ratio, i_s = procesar_imagen(ruta)
    
    fig, ax = plt.subplots(1, 1)
    
    if tipo == "axial":
        ax.imshow(volume3d[i_s[0] // 2, :, :], cmap='gray')
        ax.set_aspect(axial_aspect_ratio)
    elif tipo == "coronal":
        ax.imshow(volume3d[:, i_s[1] // 2, :], cmap='gray')
        ax.set_aspect(coronal_aspect_ratio)
    elif tipo == "sagital":
        ax.imshow(volume3d[:, :, i_s[2] // 2], cmap='gray')
        ax.set_aspect(sagital_aspect_ratio)

    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    output.seek(0)
    
    return output

@app.route("/imagen", methods=["POST"])
def mostrar_imagen():
    tipo = request.form.get("tipo_vista")
    ruta = request.form.get("ruta")
    img = generar_imagen(tipo,ruta)
    return send_file(img, mimetype='image/png')

@app.route("/imagen", methods=["GET"])
def seleccionar_imagen():
    ruta = request.args.get('ruta')
    return render_template("imagen.html",ruta = ruta)

@app.route("/mis_imagenes")
@login_required
def mis_imagenes():
    user_id = current_user.u_id
    with app.app_context():
        imagenes = Imagen.query.filter_by(u_id=user_id).all()
    return render_template("mis_imagenes.html", imagenes=imagenes)

@app.route("/")
def home():
    return render_template("home.html")

if __name__ == "__main__":
    app.run(debug=True)
