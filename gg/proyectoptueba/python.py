from tkinter import *
import serial, time, matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pygame
import numpy as np
import sys
import re

# -----------------------------
# CONFIGURACIÓN DEL PUERTO SERIE
# -----------------------------
device = 'COM6'       # Puerto donde está conectado el Arduino receptor
BAUDRATE = 9600      # Velocidad de transmisión. Debe coincidir con Arduino.

try:
    mySerial = serial.Serial(device, BAUDRATE, timeout=1)
    time.sleep(2)
    print(f"Conectado al receptor ({device}) a {BAUDRATE} baudios")
except Exception as e:
    print("Error al conectar al puerto serie:", e)
    mySerial = None

# -----------------------------
# AUDIO
# -----------------------------
pygame.mixer.init()
SONIDO_FALLO = "alerta_fallo2.mp3"

# -----------------------------
# VARIABLES GLOBALES
# -----------------------------
temperaturas, humedades, tiempo = [], [], []
temperaturasM, humedadesM, tiempoM = [], [], []
j, jM, jT, jH = 0, 0, 0, 0
contador_medias = 0
medias_tierra = False  # False = medias en satélite, True = medias en PC
sumaT, sumaH = 0, 0
grafica_iniciada = False
nuevos = 0
idx = 0
tmax, hmax = 100, 100
N = 10
tempCola = [0] * N
humCola = [0] * N

aguja, rastro, axr = None, None, None
linea_tempM, linea_temp, linea_hum, linea_humM = None, None, None, None

# Entrys globales
temp_entry = None
hum_entry = None
periodo_TH_entry = None
periodo_D_entry = None

# ======================================================
# FUNCIÓN PARA REPRODUCIR SONIDO DE FALLO
# ======================================================
def reproducir_fallo():
    try:
        pygame.mixer.music.load(SONIDO_FALLO)
        pygame.mixer.music.play()
    except Exception as e:
        print("Error reproduciendo sonido:", e)

# ======================================================
# LIMPIAR VENTANA TKINTER
# ======================================================
def limpiar_ventana():
    for widget in window.winfo_children():
        widget.destroy()

# ======================================================
# MENÚ PRINCIPAL
# ======================================================
def mostrar_menu_principal():
    limpiar_ventana()

    Label(window, text="Selecciona un sensor", font=("Courier", 22)).pack(pady=40)

    Button(window, text="Temperatura y Humedad",
           font=("Arial", 16), bg='lightblue',
           command=mostrar_interfaz_temp_hum).pack(pady=20)

    Button(window, text="Sensor de Movimiento",
           font=("Arial", 16), bg='lightgreen',
           command=mostrar_interfaz_radar).pack(pady=20)
# ======================================================
# INTERFAZ TEMPERATURA Y HUMEDAD
# ======================================================
def mostrar_interfaz_temp_hum():
    limpiar_ventana()
    global frame_grafica, fig, ax, ax2, linea_temp, linea_tempM
    global linea_hum, linea_humM, canvas
    global temp_entry, hum_entry, periodo_TH_entry

    Label(window, text="Sensor Temp/Hum", font=("Courier", 18))\
        .grid(row=0, column=0, columnspan=4, pady=10)

    frame_grafica = Frame(window, bg="white", relief="sunken", bd=2)
    frame_grafica.grid(row=1, column=0, columnspan=4, padx=10, pady=10)

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(7.5, 3.5))
    fig.subplots_adjust(wspace=0.4)

    # Líneas de lecturas
    linea_temp, = ax.plot([], [], 'r', label='T')
    linea_hum,  = ax.plot([], [], 'b', label='H')

    ax.set_ylim(20, 80)
    ax.set_xlim(0, 60)
    ax.legend()
    ax.set_title("Lecturas")
    ax.set_xlabel("Tiempo")

    # Líneas de medias
    linea_tempM, = ax2.plot([], [], 'r', label='Tmed')
    linea_humM,  = ax2.plot([], [], 'b', label='Hmed')

    ax2.set_ylim(20, 80)
    ax2.set_xlim(0, 60)
    ax2.set_title("Medias")

    # Embebemos figura en Tkinter
    canvas = FigureCanvasTkAgg(fig, master=frame_grafica)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=BOTH, expand=True)

    # Botones control
    Button(window, text="STOP", bg='orange',
           command=parar_transmision_temp_hum)\
           .grid(row=2, column=0, padx=5, pady=5)

    Button(window, text="START", bg='green',
           command=reanudar_transmision_temp_hum)\
           .grid(row=2, column=1)

    Button(window, text="Sonido", bg='red',
           command=reproducir_fallo)\
           .grid(row=2, column=2)

    Button(window, text="Volver", bg='gray',
           command=mostrar_menu_principal)\
           .grid(row=2, column=3)

    # Medias satélite / tierra
    Button(window, text="Satélite", bg='lightblue',
           command=hacer_medias_satelite)\
           .grid(row=3, column=1)

    Button(window, text="Tierra", bg='lightgreen',
           command=hacer_medias_tierra)\
           .grid(row=3, column=3)

    # Límites de medias
    Label(window, text="Temp media máx").grid(row=4, column=0)
    temp_entry = Entry(window)
    temp_entry.grid(row=4, column=1)

    Label(window, text="Hum media máx").grid(row=5, column=0)
    hum_entry = Entry(window)
    hum_entry.grid(row=5, column=1)

    def guardar_valores():
        """
        Envía 12:Tmax:Hmax al satélite.
        """
        try:
            tmax_local = float(temp_entry.get())
            hmax_local = float(hum_entry.get())
            if mySerial:
                mySerial.write(f"12:{tmax_local}:{hmax_local}\n".encode())
                print("Valores límites enviados al satélite:",
                      f"12:{tmax_local}:{hmax_local}")
        except Exception as e:
            print("Valores incorrectos:", e)

    Button(window, text="Guardar", bg="lightblue",
           command=guardar_valores)\
           .grid(row=4, column=2)

    # Periodo T/H
    Label(window, text="Periodo T/H (ms)").grid(row=6, column=0)
    periodo_TH_entry = Entry(window)
    periodo_TH_entry.grid(row=6, column=1)

    Button(window, text="Enviar periodo T/H",
           bg="lightgreen", command=enviar_nuevo_periodo_datos_temp_hum)\
           .grid(row=6, column=2, columnspan=2)

    global grafica_iniciada
    grafica_iniciada = True

    actualizar_todo()


# ======================================================
# RADAR
# ======================================================
def activar_modo_rastreo():
    """
    Enviamos 7:|113 (servo en modo barrido automático).
    """
    if mySerial:
        mySerial.write(b"7:|113\n")
        print("Modo rastreo enviado")


def mostrar_interfaz_radar():
    limpiar_ventana()
    global frame_grafica, fig, axr, aguja, rastro, canvas, grafica_iniciada
    global periodo_D_entry

    Label(window, text="Radar Distancia/Ángulo",
          font=("Courier", 18)).grid(row=0, column=0, columnspan=4, pady=10)

    frame_grafica = Frame(window, bg="white", relief="sunken", bd=2)
    frame_grafica.grid(row=1, column=0, columnspan=4, padx=10, pady=10)

    fig, axr = plt.subplots(figsize=(6, 4), subplot_kw={"polar": True})
    axr.set_thetamin(0)
    axr.set_thetamax(180)
    axr.set_ylim(0, 10)

    aguja, = axr.plot([], [], color='limegreen')
    rastro, = axr.plot([], [], 'o', color='limegreen', alpha=0.2)

    canvas = FigureCanvasTkAgg(fig, master=frame_grafica)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=BOTH, expand=True)

    Button(window, text="STOP", bg='orange',
           command=parar_transmision_dist).grid(row=2, column=0)

    Button(window, text="START", bg='green',
           command=reanudar_transmision_dist).grid(row=2, column=1)

    Button(window, text="Volver", bg='gray',
           command=mostrar_menu_principal).grid(row=2, column=2)

    Label(window, text="Periodo Dist (ms)").grid(row=4, column=0)
    periodo_D_entry = Entry(window)
    periodo_D_entry.grid(row=4, column=1)

    Button(window, text="Enviar periodo Dist",
           bg="lightblue", command=enviar_nuevo_periodo_datos_dist)\
           .grid(row=4, column=2, columnspan=2)

    Button(window, text="Modo Rastreo", bg='yellow',
           command=activar_modo_rastreo).grid(row=3, column=0)

    Label(window, text="Ángulo fijo (0–180):").grid(row=3, column=1)
    angulo_entry = Entry(window)
    angulo_entry.grid(row=3, column=2)

    def aplicar_angulo():
        """
        Envía 8:valor al satélite.
        """
        if mySerial:
            ang = angulo_entry.get().strip()
            if ang.isdigit():
                cmd = f"8:{ang}\n".encode()
                mySerial.write(cmd)
                print("Ángulo fijo enviado:", cmd)

    Button(window, text="Aplicar Ángulo", bg='lightblue',
           command=aplicar_angulo).grid(row=3, column=3)

    grafica_iniciada = True
    actualizar_todo()
# ======================================================
# ================= COMANDOS TX → SATÉLITE =============
# ======================================================

def parar_transmision_temp_hum():
    if mySerial:
        mySerial.write(b"1:|107\n")     # STOP TH

def reanudar_transmision_temp_hum():
    if mySerial:
        mySerial.write(b"2:|108\n")     # START TH

def parar_transmision_dist():
    if mySerial:
        mySerial.write(b"3:|109\n")     # STOP DIST

def reanudar_transmision_dist():
    if mySerial:
        mySerial.write(b"4:|110\n")     # START DIST

def enviar_nuevo_periodo_datos_temp_hum():
    try:
        val = int(periodo_TH_entry.get())
        if mySerial:
            mySerial.write(f"5:{val}\n".encode())
            print("Nuevo periodo TH enviado:", val)
    except:
        print("Valor incorrecto periodo TH")
        reproducir_fallo()

def enviar_nuevo_periodo_datos_dist():
    try:
        val = int(periodo_D_entry.get())
        if mySerial:
            mySerial.write(f"6:{val}\n".encode())
            print("Nuevo periodo DIST enviado:", val)
    except:
        print("Valor incorrecto periodo Dist")
        reproducir_fallo()

def hacer_medias_satelite():
    global medias_tierra
    medias_tierra = False
    if mySerial:
        mySerial.write(b"10:|155\n")   # medias en el satélite

def hacer_medias_tierra():
    global medias_tierra
    medias_tierra = True
    if mySerial:
        mySerial.write(b"11:\n")

# ======================================================
# ========== CHECKSUM Y LECTURA SERIAL =================
# ======================================================

def hacerChecksum(cadena):
    """
    Igual que Arduino:
    Suma ASCII de cada caracter % 256.
    """
    suma = 0
    for c in cadena:
        suma += ord(c)
    return suma % 256


def leer_datos_serial():
    """
    *SOLO* acepta mensajes válidos, completos y con checksum correcto.

    Esperado:
        CODIGO:VAL1:VAL2|CHECKSUM
        CODIGO:VAL1:VAL2:VAL3|CHECKSUM   (posición)
    """

    if mySerial and mySerial.in_waiting > 0:

        linea = mySerial.readline().decode('utf-8', errors='ignore').strip()

        if not linea:
            return None

        # --------------------------------------------------------
        # 1) Verificar que existe el '|'
        # --------------------------------------------------------
        if '|' not in linea:
            print("Mensaje ignorado (sin checksum):", linea)
            return None

        partes = linea.split('|')

        if len(partes) != 2:
            print("Mensaje mal formado:", linea)
            return None

        mensaje = partes[0].strip()
        checksum_str = partes[1].strip()

        # Check checksum numérico
        if not checksum_str.isdigit():
            print("Checksum inválido:", linea)
            return None

        checksum_recibido = int(checksum_str)
        checksum_local = hacerChecksum(mensaje)

        if checksum_local != checksum_recibido:
            print("Checksum incorrecto:", linea)
            return None

        # --------------------------------------------------------
        # 2) Parsear mensaje interno: CODIGO:VAL1:VAL2(:VAL3)
        # --------------------------------------------------------
        trozos = mensaje.split(':')

        codigo = trozos[0]

        # ======= TEMPERATURA / HUMEDAD =======
        if codigo == "1" and len(trozos) >= 3:
            try:
                t = float(trozos[1])
                h = float(trozos[2])
                return ("1", t, h)
            except:
                print("Error parseando TH:", linea)
                return None

        # ======= ERROR TH =======
        if codigo == "2":
            print("Error temp/hum recibido")
            reproducir_fallo()
            return None

        # ======= DISTANCIA / ANGULO =======
        if codigo == "3" and len(trozos) >= 3:
            try:
                dist = float(trozos[1])
                ang = float(trozos[2])
                return ("3", dist, ang)
            except:
                print("Error parseando dist:", linea)
                return None

        if codigo == "4":
            print("Error distancia recibido")
            reproducir_fallo()
            return None

        # ======= MEDIAS =======
        if codigo == "5" and len(trozos) >= 3:
            try:
                tM = float(trozos[1])
                hM = float(trozos[2])
                return ("5", tM, hM)
            except:
                print("Error parseando medias:", linea)
                return None

        if codigo == "6":
            print("Error en medias recibido")
            reproducir_fallo()
            return None

        # ======= POSICIÓN ORBITAL =======
        if codigo == "9" and len(trozos) >= 4:
            try:
                x = float(trozos[1])
                y = float(trozos[2])
                z = float(trozos[3])
                return ("9", x, y, z)
            except:
                print("Error parseando posición:", linea)
                return None

        print("Mensaje desconocido:", linea)
        return None

    return None
# ======================================================
# ================ ACTUALIZACIÓN GENERAL ===============
# ======================================================
def actualizar_todo():
    """
    Bucle principal de actualización (cada 100 ms):
      - Lee datos del satélite
      - Según el código, actualiza gráficas o radar
      - Si las medias se hacen en tierra, las calcula aquí
    """

    datos = leer_datos_serial()

    if datos is not None:
        codigo = datos[0]

        # -------------------- TEMPERATURA / HUMEDAD --------------------
        if codigo == "1":
            t, h = datos[1], datos[2]
            actualizar_grafica_temp_hum(t, h)

            # Si las medias se hacen en tierra:
            if medias_tierra:
                global contador_medias, sumaT, sumaH
                global idx, nuevos, jT, jH, tempCola, humCola, tmax, hmax

                # Guardamos en cola circular
                tempCola[idx] = t
                humCola[idx] = h
                idx = (idx + 1) % N

                if contador_medias < N:
                    contador_medias += 1

                nuevos += 1

                # Cuando tenemos N valores nuevos:
                if contador_medias == N and nuevos == N:

                    sumaT = sum(tempCola)
                    sumaH = sum(humCola)

                    tM = sumaT / contador_medias
                    hM = sumaH / contador_medias

                    actualizar_grafica_medias_temp_hum(tM, hM)

                    nuevos = 0

                    # Alarmas por límite de medias
                    if tM >= tmax:
                        jT += 1
                        if jT >= 3:
                            print("Error en las medias de T (PC)")
                            reproducir_fallo()
                    else:
                        jT = 0

                    if hM >= hmax:
                        jH += 1
                        if jH >= 3:
                            print("Error en las medias de H (PC)")
                            reproducir_fallo()
                    else:
                        jH = 0

        # -------------------------- RADAR (DISTANCIA/ÁNGULO) --------------------------
        elif codigo == "3":
            d, ang = datos[1], datos[2]
            actualizar_radar(d, ang)

        # -------------------------- MEDIAS DESDE SATÉLITE --------------------------
        elif codigo == "5":
            tM, hM = datos[1], datos[2]
            actualizar_grafica_medias_temp_hum(tM, hM)

        # -------------------------- POSICIÓN ORBITAL 3D --------------------------
        elif codigo == "9":
            x, y, z = datos[1], datos[2], datos[3]
            actualizar_posicion(x, y, z)

    # Re-planificar esta función dentro de 100 ms
    window.after(100, actualizar_todo)


# ======================================================
# =============== GRÁFICA TEMPERATURA/HUMEDAD ==========
# ======================================================
def actualizar_grafica_temp_hum(t, h):
    """
    Actualiza la gráfica de temperatura y humedad en tiempo real.
    """
    if linea_hum is None or linea_temp is None:
        return

    global j, temperaturas, humedades, tiempo

    temperaturas.append(t)
    humedades.append(h)
    tiempo.append(j)

    linea_temp.set_data(tiempo, temperaturas)
    linea_hum.set_data(tiempo, humedades)

    # Scroll de ventana en X
    if j < 60:
        ax.set_xlim(0, 60)
    else:
        ax.set_xlim(j - 60, j)

    ax.set_title(f"Lectura #{j}")
    j += 1

    canvas.draw()


# ======================================================
# ================ GRÁFICA DE MEDIAS ===================
# ======================================================
def actualizar_grafica_medias_temp_hum(t, h):
    """
    Actualiza la gráfica de medias (panel derecho).
    """
    if linea_humM is None or linea_tempM is None:
        return

    global jM, temperaturasM, humedadesM, tiempoM

    temperaturasM.append(t)
    humedadesM.append(h)
    tiempoM.append(jM)

    linea_tempM.set_data(tiempoM, temperaturasM)
    linea_humM.set_data(tiempoM, humedadesM)

    if jM < 60:
        ax2.set_xlim(0, 60)
    else:
        ax2.set_xlim(jM - 60, jM)

    ax2.set_title(f"Media #{jM}")
    jM += 1

    canvas.draw()


# ======================================================
# ==================== RADAR ===========================
# ======================================================
def actualizar_radar(dist, ang):
    """
    Actualiza el radar polar:
      - ang: en grados
      - dist: distancia medida (en cm o m, según lo que envíe el Arduino)
    """
    if aguja is None or rastro is None or axr is None:
        return

    ang_rad = np.deg2rad(ang)

    # Aguja
    aguja.set_data([ang_rad, ang_rad], [0, dist])
    # Punto de detección
    rastro.set_data([ang_rad], [dist])

    canvas.draw()


# ======================================================
# ================= POSICIÓN ORBITAL ===================
# ======================================================
def actualizar_posicion(x, y, z):
    """
    De momento solo mostramos por consola.
    Aquí podrías añadir una gráfica 3D en el futuro.
    """
    # print(f"Posición orbital -> x={x}, y={y}, z={z}")
    pass


# ======================================================
# ======================= MAIN =========================
# ======================================================

window = Tk()
window.geometry("850x480")
window.title("Estación de Tierra")

# Arrancamos en el menú principal
mostrar_menu_principal()

# Lanzamos el bucle de actualización general
actualizar_todo()

# Loop principal de Tkinter
window.mainloop()
