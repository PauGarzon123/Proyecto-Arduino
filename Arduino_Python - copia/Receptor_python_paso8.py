import serial
import time

# --- Configuración del Puerto Serial ---
device = 'COM5' # ¡Asegúrate que este es el puerto correcto!
BAUDRATE = 9600

mySerial = serial.Serial(device, BAUDRATE, timeout=1) 
time.sleep(2) # Espera 2 segundos para que el Arduino se reinicie y prepare
print(f"Conectado a {device}. Esperando datos del Arduino...")


# --- Bucle Principal de Lectura y Control ---
while True:
    try:
        if mySerial.in_waiting > 0:
            linea = mySerial.readline().decode('utf-8').rstrip()
            
            # Solo procesa si la línea no está vacía (asegura que recibimos algo válido)
            if linea: 
                print(f"{linea}")
                
                # Envía el comando 'P' de vuelta para el parpadeo
                mySerial.write(b'P') 
                print(" -> COMANDO ENVIADO: 'P' para parpadear")
            
        time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nPrograma terminado por el usuario.")
        mySerial.close()
        break
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
        mySerial.close()
        break