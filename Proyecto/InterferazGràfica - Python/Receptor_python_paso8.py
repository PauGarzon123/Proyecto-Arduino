from tkinter import *
import serial, time, matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
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

device = 'COM7'
BAUDRATE = 9600
mySerial = serial.Serial(device, BAUDRATE, timeout=1)
time.sleep(2)
print(f"Conectado al receptor ({device})")
hablar(f"Conectado al receptor ({device})")

pygame.mixer.init()
SONIDO_FALLO = "caballo_homo.mp3"   # tu archivo de sonido

temperaturas, humedades, tiempo = [], [], []
j = 0
grafica_iniciada = False

def reproducir_fallo():
    try:
        pygame.mixer.music.load(SONIDO_FALLO)
        pygame.mixer.music.play()
    except Exception as e:
        print("Error al reproducir el sonido:", e)
        hablar("Error al reproducir el sonido")

def EntrarClick():
    print("Has introducido:", fraseEntry.get())

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

def iniciar_grafica():
    global fig, ax, linea_temp, linea_hum, grafica_iniciada, canvas
    if grafica_iniciada:
        return
    grafica_iniciada = True

    fig, ax = plt.subplots(figsize=(4, 3))
    linea_temp, = ax.plot([], [], 'r', label='Temperatura (ºC)')
    linea_hum, = ax.plot([], [], 'b', label='Humedad (%)')
    ax.set_ylim(20, 100)
    ax.legend()
    ax.set_xlim(0, 100)
    ax.set_title("Lectura de datos DHT")

    canvas = FigureCanvasTkAgg(fig, master=frame_grafica)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=BOTH, expand=True)

    actualizar_grafica()

def actualizar_grafica():
    global j
    if not grafica_iniciada:
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
                humedades.append(h)
                tiempo.append(j)
                linea_temp.set_data(tiempo, temperaturas)
                linea_hum.set_data(tiempo, humedades)
                if j < 75:
                    ax.set_xlim(0, 100)
                else:
                    ax.set_xlim(j - 75, j + 25)
                ax.set_title(f"Lectura #{j}")
                canvas.draw()
                j += 1
            except Exception as e:
                print("Error:", e)
    window.after(100, actualizar_grafica)

window = Tk()
window.geometry("800x500")
window.title("Control Serial (Emisor-Receptor)")

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

window.mainloop()
