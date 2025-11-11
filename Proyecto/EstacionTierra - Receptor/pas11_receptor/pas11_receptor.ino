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
      int idx = datos.indexOf(':');
      int codigo = datos.substring(0, idx).toInt();
      String valor = datos.substring(idx + 1);

      if (codigo == 1) {               // Temp/Hum
        Serial.print("Temp/Hum: ");
        Serial.println(valor);
      } 
      else if (codigo == 2) {          // Fallo Temp/Hum
        Serial.println("⚠️ FALLA Temp/Hum detectada");
      } 
      else if (codigo == 3) {          // Distancia
        Serial.print("Distancia: ");
        Serial.println(valor);
      } 
      else if (codigo == 4) {          // Fallo Distancia
        Serial.println("⚠️ FALLA Distancia detectada");
      } 
      else {                           // Código desconocido
        Serial.print("Dato desconocido: ");
        Serial.println(datos);
      }
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
