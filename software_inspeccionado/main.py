from flask import Flask, render_template, request, send_file, redirect, url_for, flash, abort
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
from sqlalchemy.exc import IntegrityError
from PIL import Image, ImageEnhance
from dotenv import load_dotenv

matplotlib.use('Agg')
load_dotenv()

app = Flask(__name__)

db_user = os.getenv("PG_USER")
db_password = os.getenv("PG_PASSWORD")
db_host = os.getenv("PG_HOST")
db_name = os.getenv("PG_DBNAME")
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv("SECRET_KEY")
image_dir = os.getenv("IMAGE_DIR")
IMAGE_MIME_TYPE = 'image/png'

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
    return render_template("inicio.html", user=current_user.name)

def procesar_imagen(ruta_relativa):
    base_dir = os.path.abspath(image_dir)
    # Usa `safe_join` para crear una ruta segura y evitar path traversal
    ruta_absoluta = safe_join(base_dir, ruta_relativa)
    if not ruta_absoluta.startswith(base_dir) or not os.path.isdir(ruta_absoluta):
        # Si el archivo está fuera del directorio seguro, abortar la operación
        abort(403, description="Acceso no permitido fuera del directorio permitido")

    ct_images = [
        entry.name for entry in os.scandir(ruta_absoluta)
        if entry.is_file() and entry.name.endswith('.dcm')
    ]

    slices = [
        pydicom.dcmread(safe_join(ruta_absoluta, s), force=True)
        for s in ct_images
    ]
    
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
        array2d = s.pixel_array
        volume3d[:, :, i] = array2d

    total_frames = len(slices)
    
    return volume3d, axial_aspect_ratio, sagital_aspect_ratio, coronal_aspect_ratio, total_frames

def safe_join(base, paths):
    # Normalizar la ruta base y la ruta combinada
    base = os.path.abspath(base)
    path = os.path.abspath(os.path.join(base,paths))

    # Verificar que la ruta esté dentro de la ruta base
    if not path.startswith(base):
        abort(403, description="Acceso no permitido fuera del directorio permitido")
    return path

def generar_imagen(tipo, ruta, frame_index):
    volume3d, axial_aspect_ratio, sagital_aspect_ratio, coronal_aspect_ratio, _ = procesar_imagen(ruta)
    
    fig, ax = plt.subplots(1, 1)
    
    if tipo == "axial":
        ax.imshow(volume3d[frame_index, :, :], cmap='gray')
        ax.set_aspect(axial_aspect_ratio)
    elif tipo == "coronal":
        ax.imshow(volume3d[:, frame_index, :], cmap='gray')
        ax.set_aspect(coronal_aspect_ratio)
    elif tipo == "sagital":
        ax.imshow(volume3d[:, :, frame_index], cmap='gray')
        ax.set_aspect(sagital_aspect_ratio)

    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    output.seek(0)
    return output

@app.route("/imagen", methods=["POST"])
def mostrar_imagen():
    tipo = request.form.get("tipo_vista")
    ruta = request.form.get("ruta")
    img = generar_imagen(tipo, ruta, 0)
    return send_file(img, mimetype=IMAGE_MIME_TYPE)

@app.route("/imagen", methods=["GET"])
def seleccionar_imagen():
    ruta = request.args.get('ruta')
    _, _, _, _, total_frames = procesar_imagen(ruta)
    return render_template("imagen.html", ruta=ruta, total_frames=total_frames)

@app.route("/imagen_frame", methods=["POST"])
def imagen_frame():
    tipo = request.form.get("tipo_vista")
    ruta = request.form.get("ruta")
    frame_index = int(request.form.get("frame_index", 0))
    img = generar_imagen(tipo, ruta, frame_index)
    return send_file(img, mimetype=IMAGE_MIME_TYPE)

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

@app.route("/ajustar_contraste_imagen", methods=["POST"])
@login_required
def ajustar_contraste_imagen():
    frame_index = int(request.form.get('frame_index'))
    ruta = request.form.get('ruta')
    tipo = request.form.get('tipo_vista')
    contraste_factor = float(request.form.get('contraste_factor', 1.0))
    output = generar_imagen(tipo, ruta, frame_index)

    img_pil = Image.open(output)
    enhancer = ImageEnhance.Contrast(img_pil)
    img_contrastada = enhancer.enhance(contraste_factor)

    img_io = io.BytesIO()
    img_contrastada.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype=IMAGE_MIME_TYPE)

@app.route("/ajustar_contraste", methods=["GET"])
def mostrar_ajustar_contraste():
    ruta = request.args.get('ruta')
    tipo_vista = request.args.get('tipo_vista')
    frame_index = int(request.args.get('frame_index', 0))
    _, _, _, _, total_frames = procesar_imagen(ruta)
    return render_template("ajustar_contraste.html", ruta=ruta, tipo_vista=tipo_vista, frame_index=frame_index, total_frames=total_frames)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'imagenes-dicom')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/procesar_carpetas', methods=['POST'])
@login_required
def procesar_carpetas():
    if 'files[]' not in request.files:
        return "No se seleccionaron archivos", 400

    archivos = request.files.getlist('files[]')
    if not archivos:
        return "No hay archivos seleccionados", 400

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    for archivo in archivos:
        if archivo.filename != '':
            ruta_guardado = os.path.join(app.config['UPLOAD_FOLDER'], archivo.filename)
            print(f"Intentando guardar el archivo en: {ruta_guardado}")
            directorio = os.path.dirname(ruta_guardado)
            if not os.path.exists(directorio):
                os.makedirs(directorio)
            archivo.save(ruta_guardado)
            print(f"Archivo guardado en: {ruta_guardado}")

    return redirect(url_for('mis_imagenes'))

@app.route('/cargar_carpetas', methods=['GET'])
def cargar_carpetas():
    return render_template('cargar_carpetas.html')

if __name__ == "__main__":
    app.run(debug=True)
