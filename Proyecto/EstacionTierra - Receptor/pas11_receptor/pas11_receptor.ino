#include <SoftwareSerial.h>

SoftwareSerial enlace(10, 11);  // RX, TX (conectado al emisor)
const int led = 13;

void setup() {
  Serial.begin(9600);
  enlace.begin(9600);
  pinMode(led, OUTPUT);
  Serial.println("Estación de Tierra lista.");
}

void loop() {
  // recibir datos del emisor
  if (enlace.available() > 0) {
    digitalWrite(led, HIGH);  // 🔴 se enciende al recibir datos

    String datos = enlace.readStringUntil('\n');
    datos.trim();

    if (datos.length() > 0) {
      Serial.println(datos);
    }

    digitalWrite(led, LOW);   // 💡 se apaga justo después
  }

  // reenviar comandos al emisor
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    if (cmd.length() > 0) {
      enlace.println(cmd);
      Serial.print("Comando reenviado al emisor: ");
      Serial.println(cmd);
    }
  }
}
