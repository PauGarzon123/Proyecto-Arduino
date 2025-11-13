from tkinter import *
import serial, time, matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pygame
import numpy as np
from collections import deque

# ==========================
#   CONFIG SERIAL
# ==========================
device = 'COM6'
BAUDRATE = 9600
try:
    mySerial = serial.Serial(device, BAUDRATE, timeout=1)
    time.sleep(2)
    print(f"Conectado al receptor ({device})")
except Exception as e:
    print(" Error al conectar al puerto serie:", e)
    mySerial = None

# ==========================
#   CONFIG AUDIO
# ==========================
pygame.mixer.init()
SONIDO_FALLO = "alerta_fallo.mp3"

# ==========================
#   VARIABLES GLOBALES
# ==========================

# Datos para gráficas instantáneas
temperaturas, humedades, tiempo = [], [], []
j = 0  # índice de lectura

# Datos para gráficas de medias
tempsM, humsM, tiempoM = [], [], []
jM = 0

# Cola circular para medias EN TIERRA (últimos 10)
cola_t = deque(maxlen=10)
cola_h = deque(maxlen=10)

# Suma temporal para medias en tierra (solo por claridad)
sumaT = 0.0
sumaH = 0.0
contador_medias_local = 0

# Estado de interfaz
interfaz_temp = False
interfaz_radar = False

# Radar
aguja = None
rastro = None
axr = None
canvas = None

# Límites de medias (inicialmente muy grandes)
temperaturamediamaxima = 999.0
humedadmediamaxima = 999.0

# Widgets referencias
temp_entry = None
hum_entry = None
label_Tmax = None
label_Hmax = None
entry_periodo_th = None
entry_periodo_dist = None
label_estado_comm = None
label_error_sensores = None

# Medias: dónde se calculan
medias_en_satelite = True  # True = usar código 5:, False = calcular en tierra

# Contadores para "3 medias seguidas"
consecT = 0
consecH = 0

# Último instante de comunicación recibida (para detectar fallo)
last_comm_time = time.time()


# ==========================
#   FUNCIONES AUXILIARES
# ==========================

def reproducir_fallo():
    """Reproduce un sonido de fallo."""
    try:
        pygame.mixer.music.load(SONIDO_FALLO)
        pygame.mixer.music.play()
    except:
        pass


def mostrar_menu_principal():
    """Muestra la pantalla principal para elegir sensor."""
    limpiar_ventana()
    Label(window, text="Estación de Tierra", font=("Courier", 24, "bold")).pack(pady=10)
    Label(window, text="Selecciona el modo de visualización", font=("Arial", 14)).pack(pady=10)

    Button(window, text="Temperatura y Humedad", font=("Arial", 16, "bold"),
           bg='lightblue', command=mostrar_interfaz_temp_hum).pack(pady=10, ipadx=10, ipady=5)

    Button(window, text="Sensor de Movimiento (Radar)", font=("Arial", 16, "bold"),
           bg='lightgreen', command=mostrar_interfaz_radar).pack(pady=10, ipadx=10, ipady=5)


def limpiar_ventana():
    """Elimina todos los widgets de la ventana y marca que no hay interfaz activa."""
    global interfaz_temp, interfaz_radar
    interfaz_temp = False
    interfaz_radar = False
    for widget in window.winfo_children():
        widget.destroy()


# ==========================
#   INTERFAZ TEMP / HUM
# ==========================

def mostrar_interfaz_temp_hum():
    """Crea la interfaz con las dos gráficas (instantánea y medias),
       botones de control y campos T_max / H_max / periodos."""
    limpiar_ventana()
    global interfaz_temp, canvas, linea_temp, linea_hum, linea_tempM, linea_humM
    global ax, ax2
    global temp_entry, hum_entry, label_Tmax, label_Hmax
    global entry_periodo_th, entry_periodo_dist, label_estado_comm, label_error_sensores

    interfaz_temp = True

    Label(window, text="Sensor de Temperatura y Humedad",
          font=("Courier", 20, "bold")).grid(row=0, column=0, columnspan=6, pady=5)

    # Figura con 2 gráficas lado a lado
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(9, 4))
    fig.subplots_adjust(wspace=0.4)

    # Gráfica 1: lecturas instantáneas
    linea_temp, = ax.plot([], [], 'r', label="Temperatura")
    linea_hum,  = ax.plot([], [], 'b', label="Humedad")
    ax.set_ylim(0, 100)
    ax.set_xlim(0, 60)
    ax.set_title("Lecturas instantáneas")
    ax.set_xlabel("Tiempo")
    ax.set_ylabel("Valor")
    ax.legend()

    # Gráfica 2: medias
    linea_tempM, = ax2.plot([], [], 'r', label="T_media")
    linea_humM,  = ax2.plot([], [], 'b', label="H_media")
    ax2.set_ylim(0, 100)
    ax2.set_xlim(0, 60)
    ax2.set_title("Medias de las últimas 10 lecturas")
    ax2.set_xlabel("Tiempo")
    ax2.legend()

    frame = Frame(window)
    frame.grid(row=1, column=0, columnspan=6, sticky="nsew")
    global canvas
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=BOTH, expand=True)

    # Botones de control TH / distancia
    Button(window, text="Parar T/H", bg='orange', fg="white",
           font=("Arial", 11), command=parar_TH).grid(row=2, column=0, pady=5, padx=2)
    Button(window, text="Reanudar T/H", bg='green', fg="white",
           font=("Arial", 11), command=reanudar_TH).grid(row=2, column=1, pady=5, padx=2)

    Button(window, text="Parar Distancia", bg='orange', fg="white",
           font=("Arial", 11), command=parar_dist).grid(row=2, column=2, pady=5, padx=2)
    Button(window, text="Reanudar Distancia", bg='green', fg="white",
           font=("Arial", 11), command=reanudar_dist).grid(row=2, column=3, pady=5, padx=2)

    Button(window, text="Alarma sonido", bg='red', fg="white",
           font=("Arial", 11), command=reproducir_fallo).grid(row=2, column=4, pady=5, padx=2)

    Button(window, text="Volver al menú", bg='gray', fg="white",
           font=("Arial", 11), command=mostrar_menu_principal).grid(row=2, column=5, pady=5, padx=2)

    # Selección lugar de cálculo de medias
    Label(window, text="Calcular medias en:", font=("Arial", 11, "bold")).grid(row=3, column=0, pady=5)
    Button(window, text="Satélite", bg='lightblue', font=("Arial", 10),
           command=hacer_medias_satelite).grid(row=3, column=1, pady=5, padx=2)
    Button(window, text="Tierra", bg='lightgreen', font=("Arial", 10),
           command=hacer_medias_tierra).grid(row=3, column=2, pady=5, padx=2)

    # T_max y H_max
    Label(window, text="T_max:", font=("Arial", 11)).grid(row=4, column=0, pady=5)
    temp_entry = Entry(window, width=6)
    temp_entry.insert(0, str(int(temperaturamediamaxima)))
    temp_entry.grid(row=4, column=1)

    Label(window, text="H_max:", font=("Arial", 11)).grid(row=4, column=2, pady=5)
    hum_entry = Entry(window, width=6)
    hum_entry.insert(0, str(int(humedadmediamaxima)))
    hum_entry.grid(row=4, column=3)

    Button(window, text="Guardar límites", bg="lightblue",
           font=("Arial", 10), command=guardar_valores_limite).grid(row=4, column=4, padx=5)

    label_Tmax = Label(window, text=f"T_max actual (media): {temperaturamediamaxima}",
                       font=("Arial", 9))
    label_Tmax.grid(row=5, column=0, columnspan=3, pady=2)

    label_Hmax = Label(window, text=f"H_max actual (media): {humedadmediamaxima}",
                       font=("Arial", 9))
    label_Hmax.grid(row=5, column=3, columnspan=3, pady=2)

    # Periodos de envío
    Label(window, text="Periodo T/H (ms):", font=("Arial", 10)).grid(row=6, column=0, pady=5)
    entry_periodo_th = Entry(window, width=8)
    entry_periodo_th.insert(0, "1000")
    entry_periodo_th.grid(row=6, column=1)

    Label(window, text="Periodo Dist (ms):", font=("Arial", 10)).grid(row=6, column=2, pady=5)
    entry_periodo_dist = Entry(window, width=8)
    entry_periodo_dist.insert(0, "100")
    entry_periodo_dist.grid(row=6, column=3)

    Button(window, text="Aplicar periodos", bg="lightyellow",
           font=("Arial", 10), command=aplicar_periodos).grid(row=6, column=4, pady=5)

    # Estado comunicación
    label_estado_comm = Label(window, text="Comunicación: Desconocida", font=("Arial", 10, "bold"))
    label_estado_comm.grid(row=7, column=0, columnspan=3, pady=5)

    label_error_sensores = Label(window, text="", font=("Arial", 10), fg="red")
    label_error_sensores.grid(row=7, column=3, columnspan=3, pady=5)

    actualizar_todo()


def parar_TH():
    if mySerial:
        mySerial.write(b"1:\n")   # código 1 -> STOP T/H


def reanudar_TH():
    if mySerial:
        mySerial.write(b"2:\n")   # código 2 -> START T/H


def parar_dist():
    if mySerial:
        mySerial.write(b"3:\n")   # código 3 -> STOP distancia


def reanudar_dist():
    if mySerial:
        mySerial.write(b"4:\n")   # código 4 -> START distancia


def hacer_medias_satelite():
    """Activa el cálculo de medias en el satélite."""
    global medias_en_satelite, cola_t, cola_h, tempsM, humsM, tiempoM, jM
    medias_en_satelite = True
    cola_t.clear()
    cola_h.clear()
    tempsM.clear()
    humsM.clear()
    tiempoM.clear()
    jM = 0
    if mySerial:
        mySerial.write(b"10:\n")  # código 10: medias en satélite
    print("Medias calculadas en SATÉLITE.")


def hacer_medias_tierra():
    """Activa el cálculo de medias en tierra (cola circular)."""
    global medias_en_satelite, cola_t, cola_h, tempsM, humsM, tiempoM, jM
    medias_en_satelite = False
    cola_t.clear()
    cola_h.clear()
    tempsM.clear()
    humsM.clear()
    tiempoM.clear()
    jM = 0
    if mySerial:
        mySerial.write(b"11:\n")  # código 11: medias en tierra
    print("Medias calculadas en TIERRA.")


def guardar_valores_limite():
    """Lee T_max y H_max de los Entry, actualiza variables y etiquetas."""
    global temperaturamediamaxima, humedadmediamaxima, label_Tmax, label_Hmax
    try:
        t_val = float(temp_entry.get())
        h_val = float(hum_entry.get())
        temperaturamediamaxima = t_val
        humedadmediamaxima = h_val
        label_Tmax.config(text=f"T_max actual (media): {temperaturamediamaxima}")
        label_Hmax.config(text=f"H_max actual (media): {humedadmediamaxima}")
        print("Nuevos límites de media:", temperaturamediamaxima, humedadmediamaxima)

        # Enviar al satélite (opcional, solo por protocolo)
        if mySerial:
            cmd = f"12:{temperaturamediamaxima}:{humedadmediamaxima}\n"
            mySerial.write(cmd.encode('utf-8'))
    except ValueError:
        print("Introduce valores numéricos válidos")


def aplicar_periodos():
    """Envía al satélite los nuevos periodos de envío T/H y Distancia."""
    if not mySerial:
        return
    try:
        per_th = int(entry_periodo_th.get())
        per_dist = int(entry_periodo_dist.get())

        cmd_th = f"30:{per_th}\n"
        cmd_dist = f"31:{per_dist}\n"
        mySerial.write(cmd_th.encode('utf-8'))
        mySerial.write(cmd_dist.encode('utf-8'))
        print("Nuevos periodos enviados:", per_th, per_dist)
    except ValueError:
        print("Introduce enteros en los periodos.")


# ==========================
#   INTERFAZ RADAR
# ==========================

def mostrar_interfaz_radar():
    """Interfaz para el radar polar, con modo rastreo y orientación fija."""
    limpiar_ventana()
    global interfaz_radar, canvas, aguja, rastro, axr
    interfaz_radar = True

    Label(window, text="Radar de Distancia y Ángulo", font=("Courier", 20, "bold")).grid(row=0, column=0, columnspan=3, pady=10)

    frame = Frame(window)
    frame.grid(row=1, column=0, columnspan=3)

    fig, axr = plt.subplots(figsize=(6, 4), subplot_kw={"polar": True})
    axr.set_thetamin(0)
    axr.set_thetamax(180)
    axr.set_ylim(0, 50)
    axr.set_title("Radar (0º - 180º)")

    aguja, = axr.plot([], [], linewidth=2, color="lime")
    rastro, = axr.plot([], [], 'o', alpha=0.2, markersize=3, color="lime")

    global canvas
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack()

    # Controles de modo rastreo / ángulo fijo
    Button(window, text="Modo Rastreo", bg='lightgreen', font=("Arial", 11),
           command=enviar_modo_rastreo).grid(row=2, column=0, pady=5)

    Label(window, text="Ángulo fijo (º):", font=("Arial", 11)).grid(row=2, column=1, pady=5)
    ang_entry = Entry(window, width=5)
    ang_entry.insert(0, "90")
    ang_entry.grid(row=2, column=2, pady=5)

    def fijar_angulo():
        if mySerial:
            try:
                ang = int(ang_entry.get())
                cmd = f"41:{ang}\n"
                mySerial.write(cmd.encode('utf-8'))
                print("Fijando ángulo:", ang)
            except ValueError:
                print("Ángulo inválido")

    Button(window, text="Aplicar ángulo fijo", bg='lightblue',
           font=("Arial", 11), command=fijar_angulo).grid(row=3, column=1, pady=5)

    Button(window, text="Volver al menú principal", bg='gray', fg="white",
           font=("Arial", 12), command=mostrar_menu_principal).grid(row=4, column=1, pady=10)

    actualizar_todo()


def enviar_modo_rastreo():
    """Activa el barrido continuo en el satélite."""
    if mySerial:
        mySerial.write(b"40:\n")
        print("Modo rastreo activado.")


# ==========================
#   COMUNICACIÓN SERIAL
# ==========================

def leer_datos_serial():
    """Lee una línea del puerto serie (si hay), la separa por ':' y la devuelve en forma de lista."""
    global last_comm_time
    if mySerial and mySerial.in_waiting > 0:
        linea = mySerial.readline().decode('utf-8', 'ignore').strip()
        if not linea:
            return None
        last_comm_time = time.time()
        return linea.split(":")
    return None


# ==========================
#   BUCLE PRINCIPAL
# ==========================

def actualizar_todo():
    """Lazo principal: lee datos del serial, actualiza gráficas y estado comunicación."""
    datos = leer_datos_serial()

    if datos:
        codigo = datos[0]

        # Lecturas de T/H instantáneas
        if codigo == "1" and len(datos) >= 3 and interfaz_temp:
            t = float(datos[1])
            h = float(datos[2])
            actualizar_graf_temp(t, h)

            # Si las medias se calculan en TIERRA, aquí alimentamos la cola circular
            if not medias_en_satelite:
                actualizar_media_tierra(t, h)

        # Medias calculadas en SATÉLITE
        elif codigo == "5" and len(datos) >= 3 and interfaz_temp and medias_en_satelite:
            tM = float(datos[1])
            hM = float(datos[2])
            actualizar_graf_media(tM, hM)
            comprobar_alarmas_medias(tM, hM)

        # Datos de distancia / radar
        elif codigo == "3" and len(datos) >= 3 and interfaz_radar:
            d = float(datos[1])
            ang = float(datos[2])
            actualizar_radar(d, ang)

        # Errores de sensores
        elif codigo == "2":
            if label_error_sensores:
                label_error_sensores.config(text="Fallo en sensor T/H (código 2)")
            print("Error en datos de temp/hum (código 2)")
        elif codigo == "4":
            if label_error_sensores:
                label_error_sensores.config(text="Fallo en sensor distancia (código 4)")
            print("Error en datos de distancia (código 4)")

    # Comprobación de comunicación (falta de datos global)
    actualizar_estado_comunicacion()

    window.after(100, actualizar_todo)


def actualizar_estado_comunicacion():
    """Muestra si hay comunicación reciente con el satélite o no."""
    global label_estado_comm
    if label_estado_comm:
        dt = time.time() - last_comm_time
        if dt < 5:
            label_estado_comm.config(text="Comunicación: OK", fg="green")
        else:
            label_estado_comm.config(text="Comunicación: SIN DATOS", fg="red")


# ==========================
#   GESTIÓN GRÁFICAS T/H
# ==========================

def actualizar_graf_temp(t, h):
    """Actualiza la gráfica de lecturas instantáneas de T y H."""
    global j

    if not interfaz_temp:
        return

    temperaturas.append(t)
    humedades.append(h)
    tiempo.append(j)

    linea_temp.set_data(tiempo, temperaturas)
    linea_hum.set_data(tiempo, humedades)

    if j > 50:
        ax.set_xlim(j - 50, j + 10)

    j += 1
    canvas.draw()


def actualizar_media_tierra(t, h):
    """Actualiza la cola circular de las últimas 10 temperaturas/humedades y calcula su media."""
    global cola_t, cola_h
    cola_t.append(t)
    cola_h.append(h)

    if len(cola_t) == 10:
        tM = sum(cola_t) / 10.0
        hM = sum(cola_h) / 10.0
        actualizar_graf_media(tM, hM)
        comprobar_alarmas_medias(tM, hM)


def actualizar_graf_media(tM, hM):
    """Actualiza la gráfica de medias con un nuevo punto."""
    global jM

    tempsM.append(tM)
    humsM.append(hM)
    tiempoM.append(jM)

    linea_tempM.set_data(tiempoM, tempsM)
    linea_humM.set_data(tiempoM, humsM)

    if jM > 50:
        ax2.set_xlim(jM - 50, jM + 10)

    jM += 1
    canvas.draw()


def comprobar_alarmas_medias(tM, hM):
    """Comprueba si las medias superan los límites T_max/H_max 3 veces seguidas y controla los pines 2 y 3."""
    global temperaturamediamaxima, humedadmediamaxima
    global consecT, consecH

    if not mySerial:
        return

    # Temperatura
    if tM > temperaturamediamaxima:
        consecT += 1
        if consecT >= 3:
            # Enviar 20:1 -> encender pin 2
            mySerial.write(b"20:1\n")
            print("Alarma TEMPERATURA: pin 2 ON")
    else:
        consecT = 0
        mySerial.write(b"20:0\n")  # pin 2 OFF

    # Humedad
    if hM > humedadmediamaxima:
        consecH += 1
        if consecH >= 3:
            # Enviar 21:1 -> encender pin 3
            mySerial.write(b"21:1\n")
            print("Alarma HUMEDAD: pin 3 ON")
    else:
        consecH = 0
        mySerial.write(b"21:0\n")  # pin 3 OFF


# ==========================
#   RADAR
# ==========================

def actualizar_radar(d, ang):
    """Actualiza el radar polar con la distancia d y el ángulo ang."""
    if not interfaz_radar:
        return

    ang_rad = np.deg2rad(ang)
    aguja.set_data([ang_rad, ang_rad], [0, d])

    r = np.linspace(max(0, d - 5), d, 5)
    angs = np.full_like(r, ang_rad)
    rastro.set_data(angs, r)

    canvas.draw()


# ==========================
#   MAIN
# ==========================

window = Tk()
window.geometry("1000x600")
window.title("Estación de Tierra - Satélite")
mostrar_menu_principal()
window.mainloop()
