from flask import Flask, render_template, request, send_file
import pydicom
import os
import numpy as np
import matplotlib.pyplot as plt
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib

matplotlib.use('Agg')

app = Flask(__name__)

def procesar_imagen():
    ruta = "./DATOS_DICOM/BSSFP"
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

def generar_imagen(tipo):
    volume3d, axial_aspect_ratio, sagital_aspect_ratio, coronal_aspect_ratio,i_s = procesar_imagen()
    
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
    img = generar_imagen(tipo)
    return send_file(img, mimetype='image/png')

@app.route("/")
def index():
    return render_template("imagen.html")

if __name__ == "__main__":
    app.run(debug=True)
