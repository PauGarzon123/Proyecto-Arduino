from tkinter import *
import serial, time, matplotlib.pyplot as plt

device = 'COM5' 
BAUDRATE = 9600
mySerial = serial.Serial(device, BAUDRATE, timeout=1)
time.sleep(2)
print(f"Conectado al receptor ({device})")

temperaturas, humedades, tiempo = [], [], []
j = 0
grafica_iniciada = False

def EntrarClick():
    print("Has introducido:", fraseEntry.get())

def AClick():
    print("Iniciando gráfica...")
    iniciar_grafica()

def BClick():
    print("STOP")
    mySerial.write(b"STOP\n")

def CClick():
    print("START")
    mySerial.write(b"START\n")

def DClick():
    print("Botón D presionado.")

def iniciar_grafica():
    global fig, ax, linea_temp, linea_hum, grafica_iniciada
    if grafica_iniciada:
        return
    grafica_iniciada = True
    plt.ion()
    fig, ax = plt.subplots()
    linea_temp, = ax.plot([], [], 'r', label='Temperatura (ºC)')
    linea_hum, = ax.plot([], [], 'b', label='Humedad (%)')
    ax.set_ylim(20, 100)
    ax.legend()
    ax.set_xlim(0, 100)
    actualizar_grafica()

def actualizar_grafica():
    global j
    if not plt.fignum_exists(fig.number):
        return

    if mySerial.in_waiting > 0:
        linea = mySerial.readline().decode('utf-8', errors='ignore').strip()
        if linea.startswith("T:"):
            try:
                t, h = map(float, linea.replace("T:", "").split(":"))
                temperaturas.append(t)
                humedades.append(h)
                tiempo.append(j)
                linea_temp.set_data(tiempo, temperaturas)
                linea_hum.set_data(tiempo, humedades)
                if j < 75:
                    ax.set_xlim(0, 100)
                else:
                    ax.set_xlim(j - 75, j + 25)
                plt.title(f"Lectura #{j}")
                plt.draw()
                plt.pause(0.01)
                j += 1
            except Exception as e:
                print("Error:", e)
    window.after(100, actualizar_grafica)

# Interfaz gráfica
window = Tk()
window.geometry("400x400")
window.title("Control Serial (Emisor-Receptor)")

tituloLabel = Label(window, text="Interfaz Arduino", font=("Courier", 20, "italic"))
tituloLabel.grid(row=0, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")

fraseEntry = Entry(window)
fraseEntry.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

EntrarButton = Button(window, text="Entrar", bg='red', fg="white", command=EntrarClick)
EntrarButton.grid(row=1, column=3, padx=5, pady=5, sticky="nsew")

AButton = Button(window, text="INICIAR GRAFICA", bg='black', fg="white", command=AClick)
AButton.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")

BButton = Button(window, text="PARAR TRANSMISIÓN", bg='orange', fg="white", command=BClick)
BButton.grid(row=2, column=1, padx=5, pady=5, sticky="nsew")

CButton = Button(window, text="INICIAR TRANSMISIÓN", bg='green', fg="white", command=CClick)
CButton.grid(row=2, column=2, padx=5, pady=5, sticky="nsew")

DButton = Button(window, text="D", bg='black', fg="white", command=DClick)
DButton.grid(row=2, column=3, padx=5, pady=5, sticky="nsew")

window.mainloop()
