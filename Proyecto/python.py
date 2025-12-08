from tkinter import *
from matplotlib.image import imread
import serial, time, matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pygame
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import sys
import re
import os
import datetime

# -----------------------------
# CONFIGURACIÓN DEL PUERTO SERIE
# -----------------------------
device = 'COM9'       # Puerto donde está conectado el Arduino receptor
BAUDRATE = 9600      # Velocidad de transmisión. Debe coincidir con Arduino.

try:
    # Intentamos abrir el puerto serie
    mySerial = serial.Serial(device, BAUDRATE, timeout=1)
    time.sleep(2)  # Pequeña pausa para que el Arduino se estabilice
    print(f"Conectado al receptor ({device})")
except:
    # Si algo falla, lo indicamos (evitamos crasheo)
    print("Error al conectar al puerto serie")
    mySerial = None

# -----------------------------
# AUDIO
# -----------------------------
pygame.mixer.init()
SONIDO_FALLO = "alerta_fallo2.mp3"  # Archivo MP3 que sonará cuando haya error

# -----------------------------
# VARIABLES GLOBALES
# (Estas llevan el estado interno de las gráficas y cálculos)
# -----------------------------
temperaturas, humedades, tiempo = [], [], []  # Datos de lectura directa
temperaturasM, humedadesM, tiempoM = [], [], []  # Datos de medias
j, jM, jT, jH = 0, 0, 0, 0   # Contadores de puntos en gráficas
contador_medias = 0
medias_tierra = False  # False = se hacen en satélite, True = se hacen aquí
sumaT, sumaH = 0, 0
grafica_iniciada = False
nuevos = 0
idx = 0
tmax, hmax = 100, 100   # Límites por defecto
N = 10                  # Usamos 10 valores para hacer medias
tempCola = [0]*N        # Lista circular para medias de temperatura
humCola = [0]*N         # Lista circular para medias de humedad

# ==================== VARIABLES PARA 3D ====================
coords_3d = []       # aquí guardamos puntos (x,y,z) que llegan del satélite
fig3d = None
ax3d = None
canvas3d = None
ventana3d = None

coords_2d = []
fig2d = None
ax2d = None
canvas2d = None



# Objetos gráficos del radar
aguja, rastro, axr = None, None, None

# Líneas de las gráficas (se rellenan al crear las gráficas)
linea_tempM, linea_temp, linea_hum, linea_humM = None, None, None, None

eventos = "eventos.txt"

def registrar_evento(tipo, descripcion):
    """
    Guarda un evento en el fichero de eventos.
    tipo: 'Comando', 'Alarma', 'Observación'
    """
    ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(eventos, "a", encoding="utf-8") as f:
        f.write(f"{ahora} | {tipo} | {descripcion}\n")

def enviar_comando(mensaje, precalculado=False):
    """
    Envía un mensaje al Arduino.
    Si precalculado=True, el mensaje ya incluye '|CHECKSUM\n' 
    Si precalculado=False, calcula el checksum y lo añade automáticamente.
    """
    if precalculado:
        paquete = mensaje
    else:
        # Eliminamos \n si existe, luego añadimos checksum
        mensaje = mensaje.strip()
        checksum = hacerChecksum(mensaje)
        paquete = f"{mensaje}|{checksum}\n"

    if mySerial:
        mySerial.write(paquete.encode())
        registrar_evento("Comando", paquete.strip())
# ==================================================================
# FUNCIÓN PARA REPRODUCIR SONIDO DE FALLO y añadirlo a los eventos
# ==================================================================
def reproducir_fallo(descripcion="Alarma detectada"):
    registrar_evento("Alarma", descripcion)
    try:
        pygame.mixer.music.load(SONIDO_FALLO)
        pygame.mixer.music.play()
    except Exception as e:
        print("Error reproduciendo sonido:", e)
        registrar_evento("Alarma", "Error reproduciendo sonido")

# ======================================================
# LIMPIAR VENTANA TKINTER
# ======================================================
def limpiar_ventana():
    """
    Elimina todos los widgets de la ventana.
    Esto permite cambiar entre pantallas de interfaz.
    """
    for widget in window.winfo_children():
        widget.destroy()


# ======================================================
# MENU PRINCIPAL CON DOS BOTONES
# ======================================================
def mostrar_menu_principal():
    """
    Pantalla principal con dos opciones:
    - Sensor temperatura/humedad
    - Sensor de distancia / radar
    """
    limpiar_ventana()

    Label(window, text="Selecciona un sensor", font=("Courier", 22)).pack(pady=40)

    Button(window, text="Temperatura y Humedad",
           font=("Arial", 16), bg='lightblue',
           command=mostrar_interfaz_temp_hum).pack(pady=20)

    Button(window, text="Sensor de Movimiento",
           font=("Arial", 16), bg='lightgreen',
           command=mostrar_interfaz_radar).pack(pady=20)
    
    Button(window, text="Órbita 3D Satélite",
           font=("Arial", 16), bg='lightyellow',
           command=abrir_grafica_3d).pack(pady=20)
    
    Button(window, text="Registrar Observación", 
           font=("Arial", 16), bg='lightpink',
           command=mostrar_panel_observaciones).pack(pady=20)
    Button(window, text="Ver Registro de Eventos",
           font=("Arial", 16), bg='lightgray',
           command=mostrar_eventos).pack(pady=20)



# ======================================================
# INTERFAZ TEMPERATURA Y HUMEDAD
# ======================================================
def mostrar_interfaz_temp_hum():
    """
    Crea toda la interfaz gráfica de temperatura y humedad:
    - 2 gráficas (lecturas y medias)
    - botones ST0P/START
    - botones para elegir dónde hacer medias
    - entrada de límites máximos
    - entrada y envío de periodo T/H
    """
    limpiar_ventana()
    global frame_grafica, fig, ax, ax2, linea_temp, linea_tempM
    global linea_hum, linea_humM, canvas
    global temp_entry, hum_entry, periodo_TH_entry, periodo_D_entry

    # -------- TITULO --------
    Label(window, text="Sensor Temp/Hum", font=("Courier", 18))\
        .grid(row=0, column=0, columnspan=4, pady=10)

    # -------- ZONA DE GRAFICAS --------
    frame_grafica = Frame(window, bg="white", relief="sunken", bd=2)
    frame_grafica.grid(row=1, column=0, columnspan=4, padx=10, pady=10)

    # Creamos dos gráficas lado a lado
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(7.5, 3.5))
    fig.subplots_adjust(wspace=0.4)

    # Línea de temperatura y humedad en la gráfica principal
    linea_temp, = ax.plot([], [], 'r', label='T')
    linea_hum,  = ax.plot([], [], 'b', label='H')

    ax.set_ylim(20, 80)        # Límites verticales fijos
    ax.set_xlim(0, 60)         # Se irá moviendo según avancen muestras
    ax.legend()
    ax.set_title("Lecturas")
    ax.set_xlabel("Tiempo")

    # Gráfica derecha: medias
    linea_tempM, = ax2.plot([], [], 'r', label='Tmed')
    linea_humM,  = ax2.plot([], [], 'b', label='Hmed')

    ax2.set_ylim(20, 80)
    ax2.set_xlim(0, 60)
    ax2.set_title("Medias")

    # Insertamos figura en Tkinter
    canvas = FigureCanvasTkAgg(fig, master=frame_grafica)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=BOTH, expand=True)

    # -------- BOTONES STOP/START --------
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

    # -------- MEDIAS SATÉLITE / TIERRA --------
    Button(window, text="Satélite", bg='lightblue',
           command=hacer_medias_satelite)\
           .grid(row=3, column=1)

    Button(window, text="Tierra", bg='lightgreen',
           command=hacer_medias_tierra)\
           .grid(row=3, column=3)

    # -------- ENTRADAS DE LIMITES --------
    Label(window, text="Temp media máx").grid(row=4, column=0)
    temp_entry = Entry(window); temp_entry.grid(row=4, column=1)

    Label(window, text="Hum media máx").grid(row=5, column=0)
    hum_entry = Entry(window); hum_entry.grid(row=5, column=1)

    # Función interna para guardar límites nuevos
    def guardar_valores():
        """
        Toma los valores de temperatura/humedad máximas escritos por el
        usuario y se los envía al satélite para que active alarmas allí.
        """
        try:
            tmax = float(temp_entry.get())
            hmax = float(hum_entry.get())
            enviar_comando(f"12:{tmax}:{hmax}")
            print("Valores enviados al satélite:", f"12:{tmax}:{hmax}\n".strip())
        except:
            print("Valores incorrectos")

    Button(window, text="Guardar", bg="lightblue",
           command=guardar_valores)\
           .grid(row=4, column=2)

    # -------- PERIODO DE ENVÍO TH --------
    Label(window, text="Periodo T/H (ms)").grid(row=6, column=0)
    periodo_TH_entry = Entry(window)
    periodo_TH_entry.grid(row=6, column=1)

    Button(window, text="Enviar periodo T/H",
           bg="lightgreen", command=enviar_nuevo_periodo_datos_temp_hum)\
           .grid(row=6, column=2, columnspan=2)

    global grafica_iniciada
    grafica_iniciada = True  # Indicamos que ya hay gráfica creada

    actualizar_todo()
# ======================================================
# ===================== RADAR ==========================
# ======================================================

def activar_modo_rastreo():
    """
    Enviamos el comando 7: (con su checksum ya pre-calculado)
    Esto le dice al satélite:
    -> "pon el servo en modo barrido automático"
    Es decir, irá oscilando de 0º a 180º y vuelta.
    """
    enviar_comando("7:|113\n") # El checksum de "7:" ya está calculado
    print("Modo rastreo enviado")


def mostrar_interfaz_radar():
    """
    Pantalla donde se muestra el radar:
    - Vista polar con el punto y la aguja
    - Botones STOP/START
    - Botón de rastreo
    - Opción de ángulo fijo
    - Envío del periodo del sensor de distancia
    """
    limpiar_ventana()
    global frame_grafica, fig, axr, aguja, rastro, canvas, grafica_iniciada

    Label(window, text="Radar Distancia/Ángulo",
          font=("Courier", 18)).grid(row=0, column=0, columnspan=4, pady=10)

    # Marco contenedor de la gráfica
    frame_grafica = Frame(window, bg="white", relief="sunken", bd=2)
    frame_grafica.grid(row=1, column=0, columnspan=4, padx=10, pady=10)

    # Gráfico polar estilo radar
    fig, axr = plt.subplots(figsize=(6,4), subplot_kw={"polar": True})
    axr.set_thetamin(0)   # Límite izquierdo del radar (0°)
    axr.set_thetamax(180) # Límite derecho del radar (180°)
    axr.set_ylim(0,10)    # Rango de distancia visible

    # “Aguja” del radar (línea que apunta al ángulo)
    aguja, = axr.plot([], [], color='limegreen')
    # “Rastro” (punto donde está el objeto detectado)
    rastro, = axr.plot([], [], 'o', color='limegreen', alpha=0.2)

    canvas = FigureCanvasTkAgg(fig, master=frame_grafica)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=BOTH, expand=True)

    # Botones principales
    Button(window, text="STOP", bg='orange',
           command=parar_transmision_dist).grid(row=2, column=0)

    Button(window, text="START", bg='green',
           command=reanudar_transmision_dist).grid(row=2, column=1)

    Button(window, text="Volver", bg='gray',
           command=mostrar_menu_principal).grid(row=2, column=2)

    # Entrada del periodo de la distancia
    Label(window, text="Periodo Dist (ms)").grid(row=4, column=0)
    periodo_D_entry = Entry(window)
    periodo_D_entry.grid(row=4, column=1)

    Button(window, text="Enviar periodo Dist",
           bg="lightblue", command=enviar_nuevo_periodo_datos_dist)\
           .grid(row=4, column=2, columnspan=2)

    # Botón de rastreo
    Button(window, text="Modo Rastreo", bg='yellow',
           command=activar_modo_rastreo).grid(row=3, column=0)

    # Ángulo fijo manual
    Label(window, text="Ángulo fijo (0–180):").grid(row=3, column=1)
    angulo_entry = Entry(window)
    angulo_entry.grid(row=3, column=2)

    def aplicar_angulo():
        """
        Envía 8:valor al satélite.
        Esto fuerza al servo a quedarse inmóvil en un ángulo concreto.
        """
        ang = angulo_entry.get().strip()
        if ang.isdigit():
            enviar_comando(f"8:{ang}")
            print("Ángulo fijo enviado:", f"8:{ang}\n".strip())

    Button(window, text="Aplicar Ángulo", bg='lightblue',
           command=aplicar_angulo).grid(row=3, column=3)

    grafica_iniciada = True

    actualizar_todo()
# ======================================================
# ==================== GRÁFICA 3D ======================
# ======================================================

def abrir_grafica_3d():
    """
    Ventana con:
    - Órbita 3D
    - Órbita proyectada en mapa 2D
    - Botones: Imagen simulada / Imagen satelital
    """
    global fig3d, ax3d, canvas3d, ventana3d
    global fig2d, ax2d, canvas2d, worldmap

    ventana3d = Toplevel(window)
    ventana3d.title("Órbita del Satélite – 3D + 2D")
    ventana3d.geometry("1200x600")

    # ---------------------------
    # LAYOUT DE 2 COLUMNAS
    # ---------------------------
    frame_left = Frame(ventana3d)
    frame_left.pack(side=LEFT, fill=BOTH, expand=True)

    frame_right = Frame(ventana3d)
    frame_right.pack(side=RIGHT, fill=BOTH, expand=True)

    # ---------------------------
    # FIGURA 3D
    # ---------------------------
    fig3d = plt.figure(figsize=(5,5))
    ax3d = fig3d.add_subplot(111, projection='3d')

    # Tierra
    radio = 6371
    u = np.linspace(0, 2*np.pi, 40)
    v = np.linspace(0, np.pi, 40)
    x = radio * np.outer(np.cos(u), np.sin(v))
    y = radio * np.outer(np.sin(u), np.sin(v))
    z = radio * np.outer(np.ones(len(u)), np.cos(v))
    ax3d.plot_surface(x, y, z, color='b', alpha=0.3)

    ax3d.set_title("Órbita en 3D")

    canvas3d = FigureCanvasTkAgg(fig3d, master=frame_left)
    canvas3d.get_tk_widget().pack(fill=BOTH, expand=True)

    # ---------------------------
    # FIGURA 2D
    # ---------------------------
    fig2d, ax2d = plt.subplots(figsize=(6,4))

    # Cargar mapa mundial (lo pongo en tu carpeta actual)
    map_path = "worldmap.png"
    if not os.path.exists(map_path):
        print("⚠ worldmap.png no encontrado. Colócalo en la misma carpeta.")
    else:
        worldmap = imread(map_path)
        ax2d.imshow(worldmap, extent=[-180,180,-90,90])
    
    ax2d.set_title("Órbita proyectada en mapa mundial")
    ax2d.set_xlabel("Longitud")
    ax2d.set_ylabel("Latitud")

    canvas2d = FigureCanvasTkAgg(fig2d, master=frame_right)
    canvas2d.get_tk_widget().pack(fill=BOTH, expand=True)

    # ---------------------------
    # BOTONES
    # ---------------------------
    boton_frame = Frame(ventana3d)
    boton_frame.pack(side=BOTTOM, pady=10)

    Button(boton_frame, text="Imagen simulada",
           bg="lightblue", width=20).pack(side=LEFT, padx=20)

    Button(boton_frame, text="Imagen satelital",
           bg="lightgreen", width=20).pack(side=LEFT, padx=20)

    ventana3d.after(200, actualizar_graficas_orbitales)

def actualizar_graficas_orbitales():
    """
    Actualiza simultáneamente:
    - Gráfica 3D
    - Mapa 2D con órbita proyectada
    """
    global coords_3d, coords_2d

    if ax3d is None:
        return

    # ---------------------------
    # REINICIAR GRAFICA 3D
    # ---------------------------
    ax3d.cla()

    radio = 6371
    u = np.linspace(0, 2*np.pi, 40)
    v = np.linspace(0, np.pi, 40)
    x = radio*np.outer(np.cos(u), np.sin(v))
    y = radio*np.outer(np.sin(u), np.sin(v))
    z = radio*np.outer(np.ones(len(u)), np.cos(v))
    ax3d.plot_surface(x, y, z, color='lightblue', alpha=0.3)

    # Trayectoria 3D
    if coords_3d:
        xs = [p[0] for p in coords_3d]
        ys = [p[1] for p in coords_3d]
        zs = [p[2] for p in coords_3d]
        ax3d.plot(xs, ys, zs, color="red")
        ax3d.scatter(xs[-1], ys[-1], zs[-1], color="yellow", s=50)

    canvas3d.draw()

    # ---------------------------
    # ACTUALIZAR MAPA 2D
    # ---------------------------
    if ax2d:
        ax2d.cla()
        
        # fondo del mapa
        if os.path.exists("worldmap.png"):
            ax2d.imshow(worldmap, extent=[-180,180,-90,90])

        # Convertir puntos 3D→lat/lon
        lons, lats = [], []
        for (x,y,z) in coords_3d:
            lon = np.degrees(np.arctan2(y,x))
            lat = np.degrees(np.arcsin(z / np.sqrt(x**2+y**2+z**2)))
            lons.append(lon)
            lats.append(lat)

        if lons:
            ax2d.plot(lons, lats, color="red")
            ax2d.scatter(lons[-1], lats[-1], color="yellow", s=30)

        ax2d.set_xlim(-180, 180)
        ax2d.set_ylim(-90, 90)
        ax2d.set_title("Órbita proyectada en mapa 2D")

        canvas2d.draw()

    # repetir refresco
    ventana3d.after(200, actualizar_graficas_orbitales)

def mostrar_panel_observaciones():
    limpiar_ventana()
    Label(window, text="Observaciones del Usuario", font=("Courier", 18)).pack(pady=10)
    
    # Caja de texto para escribir la observación
    observacion_text = Text(window, height=5, width=50)
    observacion_text.pack(pady=10)

    def guardar_observacion():
        texto = observacion_text.get("1.0", END).strip()
        if texto:
            registrar_evento("Observación", texto)
            print("Observación guardada")
            observacion_text.delete("1.0", END)

    Button(window, text="Guardar Observación", bg='lightgreen', command=guardar_observacion).pack(pady=5)
    Button(window, text="Volver", bg='gray', command=mostrar_menu_principal).pack(pady=5)

def mostrar_eventos():
    limpiar_ventana()

    Label(window, text="Registro de Eventos",
          font=("Courier", 18)).pack(pady=10)

    # Filtros
    Label(window, text="Filtrar por tipo:").pack()
    tipo_var = StringVar()
    tipo_menu = OptionMenu(window, tipo_var, "Todos","Comando","Alarma","Observación")
    tipo_var.set("Todos")
    tipo_menu.pack()

    Label(window, text="Filtrar por fecha (YYYY-MM-DD):").pack()
    fecha_entry = Entry(window)
    fecha_entry.pack()

    # Cuadro de texto donde se muestran los eventos
    caja = Text(window, width=80, height=20)
    caja.pack(pady=10)

    def cargar():
        caja.delete("1.0", END)
        fecha_filtro = fecha_entry.get().strip()
        tipo_filtro = tipo_var.get()

        with open(eventos, "r", encoding="utf-8") as f:
            for linea in f:
                partes = linea.split("|")
                fecha = partes[0].strip()
                tipo = partes[1].strip()
                texto = partes[2].strip()

                if fecha_filtro and not fecha.startswith(fecha_filtro):
                    continue

                if tipo_filtro != "Todos" and tipo_filtro != tipo:
                    continue

                caja.insert(END, linea)

    Button(window, text="Aplicar filtros", command=cargar).pack(pady=5)
    Button(window, text="Volver", command=mostrar_menu_principal).pack(pady=5)
# ======================================================
# ================= COMANDOS TX → SATÉLITE =============
# ======================================================
# Estos comandos son los mensajes que enviamos nosotros
# hacia el satélite. Muchos llevan checksum ya precalculado.

def parar_transmision_temp_hum():
    """
    Le mandamos '1:' (con checksum ya pre-calculado).
    Esto dice al satélite: NO envíes más temp/hum.
    """
    enviar_comando("1:|107\n", precalculado=True)

def reanudar_transmision_temp_hum():
    """
    '2:' con checksum.
    Dice al satélite que vuelva a enviar temperatura/humedad.
    """
    enviar_comando("2:|108\n", precalculado=True)

def parar_transmision_dist():
    """
    '3:' con checksum.
    Detiene las lecturas del sensor de distancia.
    """
    enviar_comando("3:|109\n", precalculado=True)

def reanudar_transmision_dist():
    """
    '4:' con checksum.
    Reactiva la distancia.
    """
    enviar_comando("4:|110\n", precalculado=True)


def enviar_nuevo_periodo_datos_temp_hum():
    """
    Coge el valor que escribió el usuario en la caja
    y se lo manda al satélite como '5:valor'.
    Este comando NO lleva checksum porque el Arduino
    no lo exige para los mensajes que recibe.
    """
    try:
        val = int(periodo_TH_entry.get())
        enviar_comando(f"5:{val}")
    except:
        print("Valor incorrecto periodo TH")
        reproducir_fallo("Valor introducido incorrecto de periodo TH")


def enviar_nuevo_periodo_datos_dist():
    """
    Igual que arriba, pero para el sensor de distancia.
    """
    try:
        val = int(periodo_D_entry.get())
        enviar_comando(f"6:{val}")
    except:
        print("Valor incorrecto periodo Dist")
        reproducir_fallo("Valor introducido incorrecto de periodo distancia")


def hacer_medias_satelite():
    """
    El usuario decide que las medias se hagan en el satélite.
    -> Enviamos '10:' con checksum ya calculado.
    """
    global medias_tierra
    medias_tierra = False
    enviar_comando("10:|155\n", precalculado=True)


def hacer_medias_tierra():
    """
    El usuario decide que las medias las calcule el PC aquí.
    Esto NO requiere checksum.
    """
    global medias_tierra
    medias_tierra = True
    enviar_comando("11:|156\n", precalculado=True)


# ======================================================
# ========== CHECKSUM Y LECTURA SERIAL =================
# ======================================================

def hacerChecksum(cadenaf):
    """
    Calcula el checksum igual que Arduino:
    - Suma el valor ASCII de cada caracter
    - Hace módulo 256
    Así comprobamos que el mensaje no llegó corrupto.
    """
    i = 0
    suma = 0
    while (i < len(cadenaf)):
        suma += ord(cadenaf[i])
        i += 1
    return suma % 256


def leer_datos_serial():
    """
    Recibe y analiza los mensajes que manda el satélite.

    Formato esperado:
    'CODIGO:valor1:valor2|CHECKSUM'

    Ejemplos reales:
    - '1:25.1:40.0|123' → temp/hum
    - '3:180.0:45.0|200' → distancia/angulo
    - '5:27.4:38.1|150'  → medias
    - '9:X:Y:Z|111'      → posición
    """

    if mySerial and mySerial.in_waiting > 0:

        linea = mySerial.readline().decode('utf-8', errors='ignore').strip()

        if linea:
            # Separar mensaje y checksum
            trozosCheck = linea.split('|')

            # El mensaje antes del '|'
            mensaje_sin_checksum = trozosCheck[0]
            checksum_aqui = hacerChecksum(mensaje_sin_checksum)
            checksum_mensaje = trozosCheck[1]

            # Comprobamos integridad
            if checksum_aqui != int(checksum_mensaje):
                print("El checksum no coincide en el mensaje:", linea)
                reproducir_fallo("Mensaje corrupto: checksum incorrecto")
                return None

            # Ahora analizamos el mensaje real
            trozos = mensaje_sin_checksum.split(":")
            codigo = trozos[0]

            # Rozando por casos
            if codigo == "1":  # temp/hum
                return codigo, float(trozos[1]), float(trozos[2])

            elif codigo == "2":  # error temp/hum
                print("Error en los datos de temp/hum")
                reproducir_fallo("Error en datos de temperatura/humedad")
                return None

            elif codigo == "3":  # dist/ang
                return codigo, float(trozos[1]), float(trozos[2])

            elif codigo == "4":
                print("Error en los datos de dist")
                reproducir_fallo("Error en datos de distancia")
                return None

            elif codigo == "5":  # medias
                return codigo, float(trozos[1]), float(trozos[2])

            elif codigo == "6":
                print("Error en las medias")
                reproducir_fallo("Error en medias enviadas por el satélite")
                return None

            elif codigo == "8":
                print("Error en los datos del angulo (servo)")
                reproducir_fallo("Error en datos de angulo")
                return None

            elif codigo == "9":  # posición
                return codigo, float(trozos[1]), float(trozos[2]), float(trozos[3])
            
            elif codigo == "10":
                print("Error en los datos de posición del satelite")
                reproducir_fallo("Error en los datos de posición del satelite")
                return None

    return None
# ======================================================
# ================ ACTUALIZACIÓN GENERAL ===============
# ======================================================
def actualizar_todo():
    """
    Esta función es el “corazón” de la interfaz.
    Se ejecuta cada 100 ms gracias a window.after().
    Aquí:
        - Leemos si ha llegado un mensaje del satélite.
        - Dependiendo del código recibido, actualizamos
          la gráfica correcta (temp/hum, medias, radar, posición).
        - Si las medias se hacen en tierra, aquí se calculan.
    """

    datos = leer_datos_serial()

    if datos:
        codigo = datos[0]

        # -------------------- TEMPERATURA / HUMEDAD --------------------
        if codigo == "1":
            t, h = datos[1], datos[2]
            actualizar_grafica_temp_hum(t, h)

            # -----------------------------------------------
            # Si el usuario decidió que las medias se hacen en TIERRA:
            # -----------------------------------------------
            if medias_tierra:
                global contador_medias, sumaT, sumaH
                global idx, nuevos, jT, jH, tempCola, humCola, tmax, hmax

                # Guardamos los valores nuevos en la cola circular
                tempCola[idx] = t
                humCola[idx] = h
                idx = (idx + 1) % N

                if contador_medias < N:
                    contador_medias += 1

                nuevos += 1

                # -----------------------
                # Cuando hemos añadido 10 valores nuevos:
                # -----------------------
                if contador_medias == N and nuevos == N:

                    sumaT = sum(tempCola)
                    sumaH = sum(humCola)

                    tM = sumaT / contador_medias
                    hM = sumaH / contador_medias

                    actualizar_grafica_medias_temp_hum(tM, hM)

                    nuevos = 0

                    # Comprobamos límite de temperatura media
                    if tM >= tmax:
                        jT += 1
                        if jT >= 3:
                            print("Error en las medias")
                            reproducir_fallo("Temperatura media supera límite")
                    else:
                        jT = 0

                    # Comprobamos límite de humedad media
                    if hM >= hmax:
                        jH += 1
                        if jH >= 3:
                            print("Error en las medias")
                            reproducir_fallo("Humedad media supera límite")
                    else:
                        jH = 0

        # -------------------------- RADAR --------------------------
        elif codigo == "3":
            d, ang = datos[1], datos[2]
            actualizar_radar(d, ang)

        # -------------------------- MEDIAS DESDE SATÉLITE --------------------------
        elif codigo == "5":
            tM, hM = datos[1], datos[2]
            actualizar_grafica_medias_temp_hum(tM, hM)

        # -------------------------- POSICIÓN 3D --------------------------
        elif codigo == "9":
            x, y, z = datos[1], datos[2], datos[3]
            actualizar_posicion(x, y, z)

    # Volvemos a llamar a esta función dentro de 100 ms
    window.after(100, actualizar_todo)

# ======================================================
# =============== GRÁFICA TEMPERATURA/HUMEDAD ==========
# ======================================================
def actualizar_grafica_temp_hum(t, h):
    """
    Actualiza la gráfica de temperatura y humedad en tiempo real.
    Si la gráfica aún no existe (interfaz no creada), salimos.
    """
    if linea_hum is None or linea_temp is None:
        return

    global j, temperaturas, humedades, tiempo

    temperaturas.append(t)
    humedades.append(h)
    tiempo.append(j)

    # Actualizamos líneas en la gráfica
    linea_temp.set_data(tiempo, temperaturas)
    linea_hum.set_data(tiempo, humedades)

    # Si hay más de 60 muestras, hacemos scroll
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
    Igual que actualizar_grafica_temp_hum, pero para la gráfica
    de las medias (panel derecho).
    """
    if linea_humM is None or linea_tempM is None:
        return

    global jM, temperaturasM, humedadesM, tiempoM

    temperaturasM.append(t)
    humedadesM.append(h)
    tiempoM.append(jM)

    linea_tempM.set_data(tiempoM, temperaturasM)
    linea_humM.set_data(tiempoM, humedadesM)

    # Scroll si hay más de 60 muestras
    if jM < 60:
        ax2.set_xlim(0, 60)
    else:
        ax2.set_xlim(jM - 60, jM)

    ax2.set_title(f"Lectura #{jM}")
    jM += 1

    canvas.draw()

# ======================================================
# ==================== RADAR ===========================
# ======================================================
def actualizar_radar(dist, ang):
    """
    Actualiza la orientación del radar:
    - ang → ángulo en grados
    - dist → distancia medida por el sensor

    Convertimos a radianes porque matplotlib trabaja en radianes.
    """
    if aguja is None or rastro is None or axr is None:
        return

    ang_rad = np.deg2rad(ang)  # Convertimos a radianes

    # Aguja (línea desde origen hasta la distancia)
    aguja.set_data([ang_rad, ang_rad], [0, dist])

    # Punto indicando dónde está el objeto detectado
    rastro.set_data([ang_rad], [dist])

    canvas.draw()


# ======================================================
# ================= POSICIÓN ORBITAL ===================
# ======================================================
def actualizar_posicion(x, y, z):
    """
    Guarda los valores recibidos 9:x:y:z en la lista coords_3d.
    La gráfica 3D los leerá después.
    """
    coords_3d.append((x, y, z))
    if len(coords_3d) > 1500:
        coords_3d.pop(0)

# ======================================================
# ======================= MAIN =========================
# ======================================================
window = Tk()
window.geometry("850x480")
window.title("Estación de Tierra")

# Mostramos la pantalla principal al inicio
mostrar_menu_principal()

# Arrancamos el loop de Tkinter
window.mainloop()