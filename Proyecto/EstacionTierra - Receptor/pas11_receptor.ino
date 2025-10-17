#include <SoftwareSerial.h>

SoftwareSerial enlace(10, 11);  // RX, TX (conectado al emisor)

void setup() {
  Serial.begin(9600);
  enlace.begin(9600);
  Serial.println("Funciona.");
}

void loop() {
  // enviar al PC
  if (enlace.available() > 0) {
    String datos = enlace.readStringUntil('\n');
    datos.trim();
    if (datos.length() > 0) {
      Serial.println(datos);
    }
  }

  // enviar al emisor
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
