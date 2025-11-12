#include <SoftwareSerial.h>

SoftwareSerial enlace(10, 11);  // RX, TX (conectado al emisor)

void setup() {
  Serial.begin(9600);
  enlace.begin(9600);
  Serial.println("Estación de Tierra lista.");
}

void loop() {
    // recibir datos del emisor
  if (enlace.available() > 0) {
    String datos = enlace.readStringUntil('\n');
    datos.trim();
  
    if (datos.length() > 0) {
    serial.println(datos)
    }
  }

    // reenviar comandos al emisor
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd.length() > 0) {
      enlace.println(cmd);
      Serial.print("Comando reenviado al emisor: ");
      Serial.println(cmd);
    }
  }
}
