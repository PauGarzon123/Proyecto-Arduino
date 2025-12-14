import serial
import time

PUERTO = "COM9"     # << CAMBIAR por el del FTDI
BAUD = 9600

print("\nAbriendo puerto...\n")

try:
    ser = serial.Serial(PUERTO, BAUD, timeout=0.1)
    time.sleep(2)
    print("Conectado al FTDI:", PUERTO)
except Exception as e:
    print("ERROR:", e)
    exit()

print("\nLeyendo datos y enviando pruebas...\n")

ultimo_envio = time.time()

while True:
    # ----- LECTURA -----
    linea = ser.readline().decode('utf-8', errors='ignore').strip()
    if linea:
        print("RX >", linea)
