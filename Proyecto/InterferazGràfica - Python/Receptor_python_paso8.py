from tkinter import *
import serial, time, matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pygame
import numpy as np

# ==== CONFIGURACIÓN SERIAL ====
device = 'COM6'
BAUDRATE = 9600
try:
    mySerial = serial.Serial(device, BAUDRATE, timeout=1)
    time.sleep(2)
    print(f"Conectado al receptor ({device})")
except Exception as e:
    print(" Error al conectar al puerto serie:", e)
    mySerial = None

# ==== CONFIGURACIÓN AUDIO ====
pygame.mixer.init()
SONIDO_FALLO = "alerta_fallo.mp3"

# ==== VARIABLES GLOBALES ====
temperaturas, humedades, tiempo = [], [], []
j = 0
grafica_iniciada = False
temperaturamediamaxima = None
humedadmediamaxima = None

# Radar
aguja = None
rastro = None
axr = None        
# ==== FUNCIONES ====
def reproducir_fallo():
    try:
        pygame.mixer.music.load(SONIDO_FALLO)
        pygame.mixer.music.play()
    except Exception as e:
        print("Error al reproducir el sonido:", e)

def mostrar_menu_principal():
    limpiar_ventana()
    Label(window, text="Selecciona un sensor", font=("Courier", 22, "italic")).pack(pady=40)
    Button(window, text="Temperatura i Humedad", font=("Arial", 16, "bold"),
           bg='lightblue', command=mostrar_interfaz_temp_hum).pack(pady=20, ipadx=10, ipady=10)
    Button(window, text="Sensor de Movimiento", font=("Arial", 16, "bold"),
           bg='lightgreen', command=mostrar_interfaz_radar).pack(pady=20, ipadx=10, ipady=10)

def limpiar_ventana():
    for widget in window.winfo_children():
        widget.destroy()

def mostrar_interfaz_temp_hum():
    limpiar_ventana()
    global frame_grafica, fig, ax, ax2, linea_temp, linea_hum, grafica_iniciada, canvas

    titulo = Label(window, text="Sensor de Temperatura i Humedad", font=("Courier", 18, "bold"))
    titulo.grid(row=0, column=0, columnspan=4, pady=10)

    # Frame que contendrá las dos gráficas
    frame_grafica = Frame(window, bg="white", relief="sunken", bd=2)
    frame_grafica.grid(row=1, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

    # ==== FIGURA CON DOS GRÁFICAS LADO A LADO ====
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(7.5, 3.5))  # lado a lado
    fig.subplots_adjust(wspace=0.4)  # espacio entre las gráficas

    # === GRAFICA 1: Temperatura y Humedad ===
    linea_temp, = ax.plot([], [], 'r', label='Temperatura (ºC)')
    linea_hum, = ax.plot([], [], 'b', label='Humedad (%)')

    # Rango y separación vertical
    ax.set_ylim(20, 80)
    ax.set_xlim(0, 60)  # más corto para que quepa mejor
    ax.legend()
    ax.set_title("Lecturas DHT")
    ax.set_xlabel("Tiempo (s)")
    ax.set_ylabel("Valor")
    ax.axhline(50, color='gray', linestyle='--', alpha=0.4)  # línea separadora

    # === GRAFICA 2: Vacía (futura) ===
    ax2.set_title("Segunda gráfica (vacía)")
    ax2.set_xlim(0, 60)
    ax2.set_ylim(20, 80)
    ax2.set_xlabel("Tiempo (s)")
    ax2.set_ylabel("Valor")

    # Insertar la figura en Tkinter
    canvas = FigureCanvasTkAgg(fig, master=frame_grafica)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=BOTH, expand=True)

    grafica_iniciada = True
    actualizar_todo()

    # ==== BOTONES ====
    Button(window, text="Parar Gráfica", bg='orange', fg="white", font=("Arial", 12),
           command=parar_transmision).grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
    Button(window, text="Reanudar", bg='green', fg="white", font=("Arial", 12),
           command=reanudar_transmision).grid(row=2, column=1, padx=5, pady=5, sticky="nsew")
    Button(window, text="Activar Alarma", bg='red', fg="white", font=("Arial", 12),
           command=reproducir_fallo).grid(row=2, column=2, padx=5, pady=5, sticky="nsew")
    Button(window, text="Volver al menú", bg='gray', fg="white", font=("Arial", 12),
           command=mostrar_menu_principal).grid(row=2, column=3, padx=5, pady=5, sticky="nsew")

    # ==== CAMPOS NUMÉRICOS ====
    Label(window, text="Temperatura media máxima:", font=("Arial", 12)).grid(row=3, column=0, padx=5, pady=5)
    temp_entry = Entry(window)
    temp_entry.grid(row=3, column=1, padx=5, pady=5)

    Label(window, text="Humedad media máxima:", font=("Arial", 12)).grid(row=3, column=2, padx=5, pady=5)
    hum_entry = Entry(window)
    hum_entry.grid(row=3, column=3, padx=5, pady=5)


    def guardar_valores():
        global temperaturamediamaxima, humedadmediamaxima
        try:
            temperaturamediamaxima = float(temp_entry.get())
            humedadmediamaxima = float(hum_entry.get())
            print(f"Guardados: Tmax={temperaturamediamaxima}, Hmax={humedadmediamaxima}")
        except ValueError:
            print("Introduce valores numéricos válidos")

    Button(window, text="Guardar valores", bg="lightblue", font=("Arial", 12),
           command=guardar_valores).grid(row=4, column=0, columnspan=4, pady=10)

    for i in range(4):
        window.columnconfigure(i, weight=1)
    for i in range(5):
        window.rowconfigure(i, weight=1)

def mostrar_interfaz_radar():
    limpiar_ventana()
    global frame_grafica, fig, axr, aguja, rastro, canvas, grafica_iniciada

    titulo = Label(window, text="Radar de Distancia y Ángulo", font=("Courier", 18, "bold"))
    titulo.grid(row=0, column=0, columnspan=4, pady=10)

    # Frame para la gráfica
    frame_grafica = Frame(window, bg="white", relief="sunken", bd=2)
    frame_grafica.grid(row=1, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

    # Crear figura solo para radar
    fig, axr = plt.subplots(figsize=(6,4), subplot_kw={"polar": True})
    axr.set_thetamin(0)
    axr.set_thetamax(180)
    axr.set_ylim(0, 10)
    axr.set_title("Radar")
    aguja, = axr.plot([], [], color='limegreen', linewidth=1.5)
    rastro, = axr.plot([], [], 'o', color='limegreen', alpha=0.2, markersize=3)

    # Insertar figura en Tkinter
    canvas = FigureCanvasTkAgg(fig, master=frame_grafica)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=BOTH, expand=True)

    grafica_iniciada = True
    actualizar_todo()  # empieza la lectura de datos y actualización

    # Botones
    Button(window, text="Parar Radar", bg='orange', fg="white", font=("Arial", 12),
           command=parar_transmision).grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
    Button(window, text="Reanudar Radar", bg='green', fg="white", font=("Arial", 12),
           command=reanudar_transmision).grid(row=2, column=1, padx=5, pady=5, sticky="nsew")
    Button(window, text="Volver al menú", bg='gray', fg="white", font=("Arial", 12),
           command=mostrar_menu_principal).grid(row=2, column=2, padx=5, pady=5, sticky="nsew")

def parar_transmision():
    print("STOP")
    if mySerial:
        mySerial.write(b"STOP\n")

def reanudar_transmision():
    print("START")
    if mySerial:
        mySerial.write(b"START\n")

def leer_datos_serial():
    if mySerial and mySerial.in_waiting > 0:
        linea = mySerial.readline().decode('utf-8', errors='ignore').strip()
        if linea:
            trozos = linea.split(":")
            codigo = trozos[0]
            if codigo == "1":
                t = float(trozos[1])
                h = float(trozos[2])
                return codigo,t,h
            if codigo == "3":
                d = float(trozos[1])
                ang = float(trozos[2])
                return codigo,d,ang
    return None

def actualizar_todo():
    datos = leer_datos_serial()
    if datos:
        codigo = datos[0]
        if codigo == "1":
            codigo, t, h = datos
            actualizar_grafica_temp_hum(t, h)
        if codigo == "3":
            codigo, d, ang = datos
            actualizar_radar(d, ang)
    window.after(100, actualizar_todo)

def actualizar_grafica_temp_hum(t, h):
    global temperaturas, humedades, tiempo, j, linea_temp, linea_hum, ax, canvas
    temperaturas.append(t)
    humedades.append(h)
    tiempo.append(j)
    linea_temp.set_data(tiempo, temperaturas)
    linea_hum.set_data(tiempo, humedades)
    if j < 50:
        ax.set_xlim(0, 60)
    else:
        ax.set_xlim(j - 50, j + 10)
    ax.set_title(f"Lectura #{j}")
    j += 1
    canvas.draw()

def actualizar_radar(d,ang):
    global aguja, rastro, canvas
    angulo_rad = np.deg2rad(ang)
    aguja.set_data([angulo_rad, angulo_rad], [0, d])
    radios_rastro = np.linspace(max(0, d-5), d, 5)
    angulos_rastro = np.full_like(radios_rastro, angulo_rad)
    rastro.set_data(angulos_rastro, radios_rastro)
    canvas.draw()


# ==== INTERFAZ PRINCIPAL ====
window = Tk()
window.geometry("850x480")
window.title("Control Serial (Emisor-Receptor)")
mostrar_menu_principal()
window.mainloop()
