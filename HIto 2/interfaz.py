import tkinter as tk
from PIL import Image, ImageTk
from tkinter import messagebox
from tkinter import filedialog
import shutil
import os

def cambiar_vista(tipo):
    global fondo_visu, fondo_visu_label
    if tipo == "Sagital":
        fondo_visu = Image.open("fotoSagital.png")
    elif tipo == "Axial":
        fondo_visu = Image.open("fotoAxial.png")
    elif tipo == "Coronal":
        fondo_visu = Image.open("fotoCoronal.png")
    else:  # Vista 3D
        fondo_visu = Image.open("foto3D.png")

    # Actualizar la imagen del Label
    fondo_visu = ImageTk.PhotoImage(fondo_visu)
    fondo_visu_label.config(image=fondo_visu)
    fondo_visu_label.image = fondo_visu  # Guardar una referencia a la imagen



def opcion_visualizar():
    #Crear una ventana para visualizar
    global fondo_visu, fondo_visu_label
    messagebox.showinfo("Opción seleccionada", "Has seleccionado la opción 'Visualizar'")
    visu_screen = tk.Toplevel()
    visu_screen.title("Visualizar")
    visu_screen.geometry("500x500")

    #Crear la barra del menu
    menubar = tk.Menu(visu_screen)
    visu_screen.config(menu=menubar)

    opciones_menu = tk.Menu(menubar,tearoff=0)
    menubar.add_cascade(label="Vistas",menu=opciones_menu)


    # Agregar opciones al menú
    opciones_menu.add_command(label="Sagital", command=lambda: cambiar_vista("Sagital"))
    opciones_menu.add_command(label="Axial", command=lambda: cambiar_vista("Axial"))
    opciones_menu.add_command(label="Coronal", command=lambda: cambiar_vista("Coronal"))
    opciones_menu.add_command(label="Vista 3D", command=lambda: cambiar_vista("3D"))


    fondo_visu = Image.open("fondoVisu.png")
    fondo_visu = ImageTk.PhotoImage(fondo_visu)
    fondo_visu_label = tk.Label(visu_screen, image=fondo_visu)
    fondo_visu_label.place(x=0.5,y=0.5,relwidth=1,relheight=1)

def opcion_cargar_archivo():
    fileName = filedialog.askopenfilename()

    nuevaCarpeta = "NuevaCarpeta"
    if not os.path.exists(nuevaCarpeta):
        os.makedirs(nuevaCarpeta)

    shutil.move(fileName,nuevaCarpeta)


def opcion_salir():
    respuesta = messagebox.askyesno("Salir", "¿Estás seguro de que quieres salir?")
    if respuesta:
        root.destroy()

# Crear la ventana principal
root = tk.Tk()
root.title("Interfaz del Programa")
root.geometry("500x500")  # Establecer el tamaño de la ventana

logo = Image.open("fondo.png")
logo = ImageTk.PhotoImage(logo)
root.iconphoto(True, logo)

fondo = Image.open("fondoFinal.png")
fondo = ImageTk.PhotoImage(fondo)
fondo_label = tk.Label(root, image=fondo)
fondo_label.place(x=0, y=0, relwidth=1, relheight=1)  # Modificar para ocupar toda la ventana

# Crear un frame para centrar los botones verticalmente
fondo_frame = Image.open("fondo.png")
fondo_frame = ImageTk.PhotoImage(fondo_frame)
frame = tk.Frame(root)
frame.place(relx=0.5, rely=0.5, anchor="center")
fondoFrame_label = tk.Label(frame,image=fondo_frame)
fondoFrame_label.place(x=0, y=0, relwidth=1, relheight=1)

# Crear botones para cada opción
boton_mis_archivos = tk.Button(frame, text="Visualizar", command=opcion_visualizar)
boton_mis_archivos.pack(pady=10)

boton_cargar_archivo = tk.Button(frame, text="Cargar archivo", command=opcion_cargar_archivo)
boton_cargar_archivo.pack(pady=10)

boton_salir = tk.Button(frame, text="Salir", command=opcion_salir)
boton_salir.pack(pady=10)

# Ejecutar el bucle principal de la ventana
root.mainloop()