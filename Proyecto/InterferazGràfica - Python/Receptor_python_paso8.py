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
temperaturasM, humedadesM, tiempoM = [], [], []
j, jM = 0, 0
contador_medias = 0
medias_tierra = False
sumaT, sumaH = 0, 0
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
    global frame_grafica, fig, ax, ax2, linea_temp, linea_tempM, linea_hum, linea_humM, grafica_iniciada, canvas
    global temp_entry, hum_entry, periodo_TH_entry, periodo_D_entry

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
    linea_tempM, = ax2.plot([], [], 'r', label='Temperatura media (ºC)')
    linea_humM, = ax2.plot([], [], 'b', label='Humedad media (%)')

    ax2.set_title("Medias de Temperatura y Humedad")
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
           command=parar_transmision_temp_hum).grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
    Button(window, text="Reanudar", bg='green', fg="white", font=("Arial", 12),
           command=reanudar_transmision_temp_hum).grid(row=2, column=1, padx=5, pady=5, sticky="nsew")
    Button(window, text="Activar Alarma", bg='red', fg="white", font=("Arial", 12),
           command=reproducir_fallo).grid(row=2, column=2, padx=5, pady=5, sticky="nsew")
    Button(window, text="Volver al menú", bg='gray', fg="white", font=("Arial", 12),
           command=mostrar_menu_principal).grid(row=2, column=3, padx=5, pady=5, sticky="nsew")

    Button(window, text="Satélite", bg='lightblue', font=("Arial", 12),
       command= hacer_medias_satelite).grid(row=3, column=1, padx=5, pady=5, sticky="nsew")

    Button(window, text="Tierra", bg='lightgreen', font=("Arial", 12),
       command= hacer_medias_tierra).grid(row=3, column=3, padx=5, pady=5, sticky="nsew")
    
    Button(window, text="Enviar período Temp/Hum", bg="lightgreen", font=("Arial", 12),
       command=enviar_nuevo_periodo_datos_temp_hum).grid(row=6, column=2, columnspan=2, padx=5, pady=5, sticky="nsew")

    Button(window, text="Enviar período Distancia", bg="lightblue", font=("Arial", 12),
       command=enviar_nuevo_periodo_datos_dist).grid(row=7, column=2, columnspan=2, padx=5, pady=5, sticky="nsew")

    # ==== CAMPOS NUMÉRICOS ====
    Label(window, text="Temperatura media máxima:", font=("Arial", 12)).grid(row=4, column=0, padx=5, pady=5)
    temp_entry = Entry(window)
    temp_entry.grid(row=4, column=1, padx=5, pady=5)

    Label(window, text="Humedad media máxima:", font=("Arial", 12)).grid(row=5, column=0, padx=5, pady=5)
    hum_entry = Entry(window)
    hum_entry.grid(row=5, column=1, padx=5, pady=5)

    Label(window, text="Calcular medias en:", font=("Arial", 12, "bold")).grid(row=3, column=0, padx=5, pady=10)

    Label(window, text="Nuevo período Temp/Hum (ms):", font=("Arial", 12)).grid(row=6, column=0, padx=5, pady=5)
    periodo_TH_entry = Entry(window)
    periodo_TH_entry.grid(row=6, column=1, padx=5, pady=5)

    Label(window, text="Nuevo período Distancia (ms):", font=("Arial", 12)).grid(row=7, column=0, padx=5, pady=5)
    periodo_D_entry = Entry(window)
    periodo_D_entry.grid(row=7, column=1, padx=5, pady=5)


    def guardar_valores():
        global temperaturamediamaxima, humedadmediamaxima
        try:
            temperaturamediamaxima = float(temp_entry.get())
            humedadmediamaxima = float(hum_entry.get())
            print(f"Guardados: Tmax={temperaturamediamaxima}, Hmax={humedadmediamaxima}")
            envio_comando = f"12:{temperaturamediamaxima}:{humedadmediamaxima}\n"
            mySerial.write(envio_comando.encode())
            print("Valores enviados al satélite:", envio_comando.strip())
        except ValueError:
            print("Introduce valores numéricos válidos")

    Button(window, text="Guardar valores", bg="lightblue", font=("Arial", 12),
           command=guardar_valores).grid(row=4, column=2, columnspan=4, pady=10)

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
           command=parar_transmision_dist).grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
    Button(window, text="Reanudar Radar", bg='green', fg="white", font=("Arial", 12),
           command=reanudar_transmision_dist).grid(row=2, column=1, padx=5, pady=5, sticky="nsew")
    Button(window, text="Volver al menú", bg='gray', fg="white", font=("Arial", 12),
           command=mostrar_menu_principal).grid(row=2, column=2, padx=5, pady=5, sticky="nsew")

def parar_transmision_temp_hum():
    print("STOP")
    if mySerial:
        mySerial.write(b"1:\n")

def reanudar_transmision_temp_hum():
    print("START")
    if mySerial:
        mySerial.write(b"2:\n")

def parar_transmision_dist():
    print("STOP")
    if mySerial:
        mySerial.write(b"3:\n")

def reanudar_transmision_dist():
    print("START")
    if mySerial:
        mySerial.write(b"4:\n")

def enviar_nuevo_periodo_datos_temp_hum():
    if mySerial:
            nuevo_periodo_TH = int(periodo_TH_entry.get())
            envio_comando = f"5:{nuevo_periodo_TH}\n"
            mySerial.write(envio_comando.encode())
            print("Valores enviados al satélite:", envio_comando.strip())

def enviar_nuevo_periodo_datos_dist():
    if mySerial:
            nuevo_periodo_D = int(periodo_D_entry.get())
            envio_comando = f"6:{nuevo_periodo_D}\n"
            mySerial.write(envio_comando.encode())
            print("Valores enviados al satélite:", envio_comando.strip())

def hacer_medias_satelite():
    global medias_tierra, contador_medias, sumaT, sumaH
    print("Medias satelite")
    if mySerial:
        mySerial.write(b"10:\n")
    medias_tierra = False
    contador_medias = 0
    sumaT = 0
    sumaH = 0

def hacer_medias_tierra():
    global medias_tierra, contador_medias, sumaT, sumaH
    print("Medias tierra")
    if mySerial:
        mySerial.write(b"11:\n")
    medias_tierra = True
    contador_medias = 0
    sumaT = 0
    sumaH = 0

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
            if codigo == "2":
                print("Error en los datos de temp/hum")
            if codigo == "3":
                d = float(trozos[1])
                ang = float(trozos[2])
                return codigo,d,ang
            if codigo == "4":
                print("Error en los datos de distancia")
            if codigo == "5":
                tM = float(trozos[1])
                hM = float(trozos[2])
                return codigo,tM,hM
            if codigo == "6":
                print("Error en las medias")
    return None

def actualizar_todo():
    datos = leer_datos_serial()
    if datos:
        codigo = datos[0]
        if codigo == "1":
            codigo, t, h = datos
            actualizar_grafica_temp_hum(t, h)
            global contador_medias, sumaT, sumaH
            contador_medias = contador_medias + 1
            sumaT = sumaT + t
            sumaH = sumaH + h
            #Calcular medias
            if(medias_tierra == True and contador_medias == 10):
                tM = sumaT/10
                tH = sumaH/10
                actualizar_grafica_medias_temp_hum(tM,tH)
                sumaT = 0
                sumaH = 0
                contador_medias = 0
        if codigo == "3":
            codigo, d, ang = datos
            actualizar_radar(d, ang)
        if codigo == "5":
            codigo, tM, hM = datos
            actualizar_grafica_medias_temp_hum(tM, hM)
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


def actualizar_grafica_medias_temp_hum(t, h):
    global temperaturasM, humedadesM, tiempoM, jM, linea_tempM, linea_humM, ax2, canvas
    temperaturasM.append(t)
    humedadesM.append(h)
    tiempoM.append(jM)
    linea_tempM.set_data(tiempoM, temperaturasM)
    linea_humM.set_data(tiempoM, humedadesM)
    if jM < 50:
        ax2.set_xlim(0, 60)
    else:
        ax2.set_xlim(jM - 50, jM + 10)
    ax2.set_title(f"Lectura #{jM}")
    jM += 1
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
