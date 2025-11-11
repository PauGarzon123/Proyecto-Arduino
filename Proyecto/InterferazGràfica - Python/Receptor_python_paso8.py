from tkinter import *
import serial, time, matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
<<<<<<< HEAD
import pygame
=======
import pygame  # para reproducir audio
import pyttsx3
# Inicializar motor de voz
voz_engine = pyttsx3.init()
voz_engine.setProperty('rate', 160)   # velocidad de la voz
voz_engine.setProperty('volume', 1)   # volumen máximo

def hablar(texto):
    try:
        voz_engine.say(texto)
        voz_engine.runAndWait()
    except Exception as e:
        print("Error al reproducir voz:", e)
>>>>>>> 8377d309a02169e76715dd6afb8791a22fd276c8

# ==== CONFIGURACIÓN SERIAL ====
device = 'COM6'
BAUDRATE = 9600
<<<<<<< HEAD
try:
    mySerial = serial.Serial(device, BAUDRATE, timeout=1)
    time.sleep(2)
    print(f"Conectado al receptor ({device})")
except Exception as e:
    print("⚠️ Error al conectar al puerto serie:", e)
    mySerial = None
=======
mySerial = serial.Serial(device, BAUDRATE, timeout=1)
time.sleep(2)
print(f"Conectado al receptor ({device})")
hablar(f"Conectado al receptor ({device})")
>>>>>>> 8377d309a02169e76715dd6afb8791a22fd276c8

# ==== CONFIGURACIÓN AUDIO ====
pygame.mixer.init()
<<<<<<< HEAD
SONIDO_FALLO = "alerta_fallo.mp3"
=======
SONIDO_FALLO = "caballo_homo.mp3"   # tu archivo de sonido
>>>>>>> 8377d309a02169e76715dd6afb8791a22fd276c8

# ==== VARIABLES GLOBALES ====
temperaturas, humedades, tiempo = [], [], []
j = 0
grafica_iniciada = False
temperaturamediamaxima = None
humedadmediamaxima = None

# ==== FUNCIONES ====
def reproducir_fallo():
    try:
        pygame.mixer.music.load(SONIDO_FALLO)
        pygame.mixer.music.play()
    except Exception as e:
        print("Error al reproducir el sonido:", e)
        hablar("Error al reproducir el sonido")

def mostrar_menu_principal():
    limpiar_ventana()
    Label(window, text="Selecciona un sensor", font=("Courier", 22, "italic")).pack(pady=40)
    Button(window, text="🌡️ Temperatura i Humedad", font=("Arial", 16, "bold"),
           bg='lightblue', command=mostrar_interfaz_temp_hum).pack(pady=20, ipadx=10, ipady=10)
    Button(window, text="🚶 Sensor de Movimiento", font=("Arial", 16, "bold"),
           bg='lightgreen', command=lambda: print("Sensor movimiento (pendiente)")).pack(pady=20, ipadx=10, ipady=10)

<<<<<<< HEAD
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
=======
def IniciarGraficaClick():
    print("Iniciando gráfica embebida...")
    hablar("Iniciando gráfica embebida")
    iniciar_grafica()

def PararTransmisionGraficaClick():
    print("STOP")
    mySerial.write(b"1:\n")

def IniciarTransmisionGraficaClick():
    print("START")
    mySerial.write(b"2:\n")

def ActivarAlarmaClick():
    print("⚠️ Alarma manual activada")
    reproducir_fallo()
>>>>>>> 8377d309a02169e76715dd6afb8791a22fd276c8

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
    actualizar_grafica(ax, canvas)

    # ==== BOTONES ====
    Button(window, text="⏸️ Parar Gráfica", bg='orange', fg="white", font=("Arial", 12),
           command=parar_transmision).grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
    Button(window, text="▶️ Reanudar", bg='green', fg="white", font=("Arial", 12),
           command=reanudar_transmision).grid(row=2, column=1, padx=5, pady=5, sticky="nsew")
    Button(window, text="🚨 Activar Alarma", bg='red', fg="white", font=("Arial", 12),
           command=reproducir_fallo).grid(row=2, column=2, padx=5, pady=5, sticky="nsew")
    Button(window, text="⬅️ Volver al menú", bg='gray', fg="white", font=("Arial", 12),
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
            print(f"✅ Guardados: Tmax={temperaturamediamaxima}, Hmax={humedadmediamaxima}")
        except ValueError:
            print("⚠️ Introduce valores numéricos válidos")

    Button(window, text="💾 Guardar valores", bg="lightblue", font=("Arial", 12),
           command=guardar_valores).grid(row=4, column=0, columnspan=4, pady=10)

    for i in range(4):
        window.columnconfigure(i, weight=1)
    for i in range(5):
        window.rowconfigure(i, weight=1)

def parar_transmision():
    print("STOP")
    if mySerial:
        mySerial.write(b"STOP\n")

def reanudar_transmision():
    print("START")
    if mySerial:
        mySerial.write(b"START\n")

def actualizar_grafica(ax, canvas):
    global j
    if not grafica_iniciada or not mySerial:
        return

    if mySerial.in_waiting > 0:
        linea = mySerial.readline().decode('utf-8', errors='ignore').strip()
        trozos = linea.split(":")
        codigo = trozos[0]

        if codigo == "2":
            print("⚠️ Aviso de fallo recibido")
            reproducir_fallo()
            hablar("Atención. Se ha detectado un fallo en el sistema.")
        elif codigo == "1":
            try:
                t = float(trozos[1])
                h = float(trozos[2])
                temperaturas.append(t)
                humedades.append(h - 5)  # pequeña separación entre líneas
                tiempo.append(j)

                linea_temp.set_data(tiempo, temperaturas)
                linea_hum.set_data(tiempo, humedades)

                if j < 50:
                    ax.set_xlim(0, 60)
                else:
                    ax.set_xlim(j - 50, j + 10)

                ax.set_title(f"Lectura #{j}")
                canvas.draw()
                j += 1
            except Exception as e:
                print("Error:", e)

    window.after(100, lambda: actualizar_grafica(ax, canvas))

# ==== INTERFAZ PRINCIPAL ====
window = Tk()
window.geometry("850x480")
window.title("Control Serial (Emisor-Receptor)")
<<<<<<< HEAD
mostrar_menu_principal()
=======

tituloLabel = Label(window, text="Interfaz Arduino", font=("Courier", 20, "italic"))
tituloLabel.grid(row=0, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")

fraseEntry = Entry(window)
fraseEntry.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

EntrarButton = Button(window, text="Entrar", bg='red', fg="white", command=EntrarClick)
EntrarButton.grid(row=1, column=3, padx=5, pady=5, sticky="nsew")

IniciarGraficaButton = Button(window, text="INICIAR GRAFICA", bg='black', fg="white", command=IniciarGraficaClick)
IniciarGraficaButton.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")

PararTransmisionGraficaButton = Button(window, text="PARAR TRANSMISIÓN", bg='orange', fg="white", command=PararTransmisionGraficaClick)
PararTransmisionGraficaButton.grid(row=2, column=1, padx=5, pady=5, sticky="nsew")

IniciarTransmisionGraficaButton = Button(window, text="INICIAR TRANSMISIÓN", bg='green', fg="white", command=IniciarTransmisionGraficaClick)
IniciarTransmisionGraficaButton.grid(row=2, column=2, padx=5, pady=5, sticky="nsew")

ActivarAlarmaButton = Button(window, text="ACTIVAR ALARMA", bg='red', fg="white", command=ActivarAlarmaClick)
ActivarAlarmaButton.grid(row=2, column=3, padx=5, pady=5, sticky="nsew")

frame_grafica = Frame(window, bg="white", relief="sunken", bd=2)
frame_grafica.grid(row=3, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

for i in range(4):
    window.columnconfigure(i, weight=1)
for i in range(4):
    window.rowconfigure(i, weight=1)

>>>>>>> 8377d309a02169e76715dd6afb8791a22fd276c8
window.mainloop()
