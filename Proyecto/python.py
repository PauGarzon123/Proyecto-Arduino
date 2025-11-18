from tkinter import *
import serial, time, matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pygame
import numpy as np

# ==== CONFIG SERIAL ====
device = 'COM4'
BAUDRATE = 9600
try:
    mySerial = serial.Serial(device, BAUDRATE, timeout=1)
    time.sleep(2)
    print(f"Conectado al receptor ({device})")
except:
    print("Error al conectar al puerto serie")
    mySerial = None

# ==== AUDIO ====
pygame.mixer.init()
SONIDO_FALLO = "alerta_fallo2.mp3"

# ==== VARIABLES ====
temperaturas, humedades, tiempo = [], [], []
temperaturasM, humedadesM, tiempoM = [], [], []
j, jM = 0, 0
contador_medias = 0
medias_tierra = False
sumaT, sumaH = 0, 0
grafica_iniciada = False
nuevos = 0
idx = 0
N = 10
tempCola = [0]*N
humCola = [0]*N

aguja = None
rastro = None
axr = None

linea_tempM = None
linea_temp = None
linea_hum = None
linea_humM = None


def reproducir_fallo(): #Reproduce el sonido de fallo. No tiene parametros. No produce un resultado.
    try:
        pygame.mixer.music.load(SONIDO_FALLO)
        pygame.mixer.music.play()
    except Exception as e:
        print("Error reproduciendo sonido:", e)


def limpiar_ventana(): #TKINTER. Elimina los objetos de la ventana abierta. No tiene parametros. No produce un resultado.
    for widget in window.winfo_children():
        widget.destroy()

def mostrar_menu_principal(): #TKINTER. Muestra el menú principal, con los dos botones para acceder a los menús de temperatura/humedad y distancia. No tiene parametros. No produce un resultado.
    limpiar_ventana()
    Label(window, text="Selecciona un sensor", font=("Courier", 22)).pack(pady=40)

    Button(window, text="Temperatura y Humedad",
           font=("Arial", 16), bg='lightblue',
           command=mostrar_interfaz_temp_hum).pack(pady=20)

    Button(window, text="Sensor de Movimiento",
           font=("Arial", 16), bg='lightgreen',
           command=mostrar_interfaz_radar).pack(pady=20)

def mostrar_interfaz_temp_hum(): #TKINTER. Muestra la interfaz de temperatura/humedad. No tiene parametros. No produce un resultado.
    limpiar_ventana()
    global frame_grafica, fig, ax, ax2, linea_temp, linea_tempM
    global linea_hum, linea_humM, canvas
    global temp_entry, hum_entry, periodo_TH_entry, periodo_D_entry

    Label(window, text="Sensor Temp/Hum", font=("Courier", 18)).grid(row=0, column=0, columnspan=4, pady=10)

    frame_grafica = Frame(window, bg="white", relief="sunken", bd=2)
    frame_grafica.grid(row=1, column=0, columnspan=4, padx=10, pady=10)

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(7.5, 3.5))
    fig.subplots_adjust(wspace=0.4)

    linea_temp, = ax.plot([], [], 'r', label='T')
    linea_hum,  = ax.plot([], [], 'b', label='H')
    ax.set_ylim(20, 80); ax.set_xlim(0, 60)
    ax.legend(); ax.set_title("Lecturas"); ax.set_xlabel("Tiempo")

    linea_tempM, = ax2.plot([], [], 'r', label='Tmed')
    linea_humM,  = ax2.plot([], [], 'b', label='Hmed')
    ax2.set_ylim(20,80); ax2.set_xlim(0,60)
    ax2.set_title("Medias")

    canvas = FigureCanvasTkAgg(fig, master=frame_grafica)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=BOTH, expand=True)

    # BOTONES
    Button(window, text="STOP", bg='orange', command=parar_transmision_temp_hum)\
        .grid(row=2, column=0, padx=5, pady=5)
    Button(window, text="START", bg='green', command=reanudar_transmision_temp_hum)\
        .grid(row=2, column=1)

    Button(window, text="Sonido", bg='red', command=reproducir_fallo)\
        .grid(row=2, column=2)
    Button(window, text="Volver", bg='gray', command=mostrar_menu_principal)\
        .grid(row=2, column=3)

    # Selección donde calcular medias
    Button(window, text="Satélite", bg='lightblue', command=hacer_medias_satelite)\
        .grid(row=3, column=1)
    Button(window, text="Tierra", bg='lightgreen', command=hacer_medias_tierra)\
        .grid(row=3, column=3)

    # Entradas valores limites
    Label(window, text="Temp media máx").grid(row=4, column=0)
    temp_entry = Entry(window); temp_entry.grid(row=4, column=1)

    Label(window, text="Hum media máx").grid(row=5, column=0)
    hum_entry = Entry(window); hum_entry.grid(row=5, column=1)

    def guardar_valores(): #Guarda y envia los valores de temperatura y humedad maximos que se han introducido por el usuario. No tiene parametros. No produce un resultado.
        try:
            tmax = float(temp_entry.get())
            hmax = float(hum_entry.get())
            if mySerial:
                mySerial.write(f"12:{tmax}:{hmax}\n".encode())
                print("Valores enviados al satélite:", f"12:{tmax}:{hmax}\n".strip())
        except:
            print("Valores incorrectos")

    Button(window, text="Guardar", bg="lightblue", command=guardar_valores)\
        .grid(row=4, column=2)
    Label(window, text="Periodo T/H (ms)").grid(row=6, column=0)
    periodo_TH_entry = Entry(window); periodo_TH_entry.grid(row=6, column=1)

    Button(window, text="Enviar periodo T/H",
           bg="lightgreen", command=enviar_nuevo_periodo_datos_temp_hum)\
           .grid(row=6, column=2, columnspan=2)


    global grafica_iniciada
    grafica_iniciada = True
    actualizar_todo()


# ===================== RADAR =======================

def activar_modo_rastreo(): #Activa el modo rastreo. No tiene parametros. Envia al satelite el mensaje "7:".
    if mySerial:
        mySerial.write(b"7:\n")
        print("Modo rastreo enviado")

def mostrar_interfaz_radar(): #TKINTER. Muestra la interfaz del radar. No tiene parametros. No produce un resultado.
    limpiar_ventana()
    global frame_grafica, fig, axr, aguja, rastro, canvas, grafica_iniciada

    Label(window, text="Radar Distancia/Ángulo",
          font=("Courier", 18)).grid(row=0, column=0, columnspan=4, pady=10)

    frame_grafica = Frame(window, bg="white", relief="sunken", bd=2)
    frame_grafica.grid(row=1, column=0, columnspan=4, padx=10, pady=10)

    fig, axr = plt.subplots(figsize=(6,4), subplot_kw={"polar": True})
    axr.set_thetamin(0); axr.set_thetamax(180)
    axr.set_ylim(0,10)
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
    periodo_D_entry = Entry(window); periodo_D_entry.grid(row=4, column=1)

    Button(window, text="Enviar periodo Dist",
           bg="lightblue", command=enviar_nuevo_periodo_datos_dist)\
           .grid(row=4, column=2, columnspan=2)

    # BOTÓN RASTREO
    Button(window, text="Modo Rastreo", bg='yellow',
           command=activar_modo_rastreo).grid(row=3, column=0)

    # ÁNGULO FIJO
    Label(window, text="Ángulo fijo (0–180):").grid(row=3, column=1)
    angulo_entry = Entry(window); angulo_entry.grid(row=3, column=2)

    def aplicar_angulo(): #Activa el modo angulo fijo y pone el sensor de distancia en un angulo introducido por el usuario. No tiene parametros. Envia al satelite el mensaje "8:angulo" (angulo siendo un numero en grados).
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

# ====================== COMANDOS ===================== 
#En los mensajes que envia la estacion tierra al satelite (estos) es importante el \n, ya que el satelite lee mensajes hasta que llega al \n, sin este nunca acaba de leer el mensaje.


def parar_transmision_temp_hum(): #Para la transmision de temp/hum. No tiene parametros. Envia al satelite el mensaje "1:\n".
    if mySerial: 
        mySerial.write(b"1:\n")

def reanudar_transmision_temp_hum(): #Renauda la transmision de temp/hum. No tiene parametros. Envia al satelite el mensaje "2:\n".
    if mySerial: 
        mySerial.write(b"2:\n")

def parar_transmision_dist(): #Para la transmision de dist. No tiene parametros. Envia al satelite el mensaje "3:\n".
    if mySerial: 
        mySerial.write(b"3:\n")

def reanudar_transmision_dist(): #Renauda la transmision de dist. No tiene parametros. Envia al satelite el mensaje "4:\n".
    if mySerial: 
        mySerial.write(b"4:\n")

def enviar_nuevo_periodo_datos_temp_hum(): #Pone un nuevo periodo de transmision de datos de temp/hum introducido por el usuario. No tiene parametros. Envia al satelite el mensaje "5:periodo\n" (periodo siendo un numero).
    try:
        val = int(periodo_TH_entry.get())
        if mySerial: 
            mySerial.write(f"5:{val}\n".encode())
    except:
        print("Valor incorrecto periodo TH")
        reproducir_fallo()

def enviar_nuevo_periodo_datos_dist(): #Pone un nuevo periodo de transmision de datos de dist introducido por el usuario. No tiene parametros. Envia al satelite el mensaje "6:periodo\n" (periodo siendo un numero).
    try:
        val = int(periodo_D_entry.get())
        if mySerial: 
            mySerial.write(f"6:{val}\n".encode())
    except:
        print("Valor incorrecto periodo Dist")
        reproducir_fallo()

def hacer_medias_satelite(): #Hace que las medias se hagan en el satelite y se paren de hacer en la estacion tierra. No tiene parametros. Envia al satelite el mensaje "10:".
    global medias_tierra
    medias_tierra = False
    if mySerial: mySerial.write(b"10:\n")

def hacer_medias_tierra(): #Hace que las medias se hagan en el tierra y se paren de hacer en el satelite. No tiene parametros. Envia al satelite el mensaje "11:".
    global medias_tierra
    medias_tierra = True
    if mySerial: mySerial.write(b"11:\n")


    # ====================== LECTURA SERIAL ======================
    
def leer_datos_serial(): #Recoge los mensajes que le llegan del satelite, saca su codigo y sus datos. No tiene parametros. Devuelve el codigo y dos datos (o None si es uno que marca error).
    if mySerial and mySerial.in_waiting > 0:
        linea = mySerial.readline().decode('utf-8', errors='ignore').strip()
        if linea:
            trozos = linea.split(":")
            codigo = trozos[0]

            if codigo == "1":   # temp/hum
                return codigo, float(trozos[1]), float(trozos[2])
            elif codigo == "2":   # error datos temp/hum
                print("Error en los datos de temp/hum")
                reproducir_fallo()
                return None
            elif codigo == "3":   # distancia
                return codigo, float(trozos[1]), float(trozos[2])
            elif codigo == "4":   # error datos dist
                print("Error en los datos de dist")
                reproducir_fallo()
                return None
            elif codigo == "5":   # medias
                return codigo, float(trozos[1]), float(trozos[2])
            elif codigo == "6":   # error en las medias
                print("Error en las medias")
                reproducir_fallo()
                return None
    return None

# ====================== ACTUALIZACIÓN ======================

def actualizar_todo(): #Lee los datos que le llegan, segun el codigo mete los datos donde corresponde y llama a la funcion de actualizar grafica correspondiente. No tiene parametros. No produce un resultado.
    datos = leer_datos_serial()
    if datos:
        codigo = datos[0]

        if codigo == "1":  # temp/hum
            t, h = datos[1], datos[2]
            actualizar_grafica_temp_hum(t,h)

            if medias_tierra:
                global contador_medias, sumaT, sumaH
                tempCola[idx] = t
                humCola[idx] = h
                idx = (idx + 1)%N
                if(contador_medias < N): contador_medias = contador_medias + 1

                nuevos = nuevos + 1

                if contador_medias == N and nuevos == N:
                    for(int i = 0)
                    SumaT = 
        

                actualizar_grafica_medias_temp_hum(tM,hM)


        elif codigo == "3": # radar
            d, ang = datos[1], datos[2]
            actualizar_radar(d,ang)

        elif codigo == "5": # medias satélite
            tM, hM = datos[1], datos[2]
            actualizar_grafica_medias_temp_hum(tM,hM)

    window.after(100, actualizar_todo)

def actualizar_grafica_temp_hum(t,h): #Primero comprueba si existen los objetos de la grafica (osea si se ha iniciado), y si sí existen, actualiza la grafica de temp/hum. Tiene como parametros (temperatura, humedad). No produce un resultado.
    if linea_hum is None or linea_temp is None: return
    global j, temperaturas, humedades, tiempo
    temperaturas.append(t); 
    humedades.append(h); 
    tiempo.append(j)

    linea_temp.set_data(tiempo, temperaturas)
    linea_hum.set_data(tiempo, humedades)

    if j < 60: 
        ax.set_xlim(0,60)
    else: 
        ax.set_xlim(j-60, j)
    ax.set_title(f"Lectura #{j}")
    j += 1

    canvas.draw()

def actualizar_grafica_medias_temp_hum(t,h): #Primero comprueba si existen los objetos de la grafica (osea si se ha iniciado), y si sí existen, actualiza la grafica de medias temp/hum. Tiene como parametros (temperatura media, humedad media). No produce un resultado.
    if linea_humM is None or linea_tempM is None: return
    global jM, temperaturasM, humedadesM, tiempoM
    temperaturasM.append(t); 
    humedadesM.append(h); 
    tiempoM.append(jM)

    linea_tempM.set_data(tiempoM, temperaturasM)
    linea_humM.set_data(tiempoM, humedadesM)

    if jM < 60: 
        ax2.set_xlim(0,60)
    else: 
        ax2.set_xlim(jM-60, jM)
    ax2.set_title(f"Lectura #{jM}")
    jM += 1

    canvas.draw()

def actualizar_radar(dist, ang): #Primero comprueba si existen los objetos de la grafica (osea si se ha iniciado), y si sí existen, actualiza la grafica de ditancia. Tiene como parametros (distancia, angulo). No produce un resultado.
    if aguja is None or rastro is None or axr is None: return
    ang_rad = np.deg2rad(ang)
    aguja.set_data([ang_rad, ang_rad], [0, dist])
    rastro.set_data([ang_rad], [dist])
    canvas.draw()

# ====================== MAIN ======================

window = Tk()
window.geometry("850x480")
window.title("Estación de Tierra")
mostrar_menu_principal()
window.mainloop()

