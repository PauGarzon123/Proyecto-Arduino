#include <SoftwareSerial.h>

SoftwareSerial enlace(10, 11);  // RX, TX (conectado al emisor)

const int led     = 13;
const int pinTemp = 2;  // alarma temperatura
const int pinHum  = 3;  // alarma humedad
const int pinRxTH = 4;  // indica que llegan datos de temperatura/humedad
const int pinRxD  = 5;  // indica que llegan datos de distancia

void setup() {
  Serial.begin(9600);
  enlace.begin(9600);

  pinMode(led, OUTPUT);
  pinMode(pinTemp, OUTPUT);
  pinMode(pinHum, OUTPUT);
  pinMode(pinRxTH, OUTPUT);
  pinMode(pinRxD, OUTPUT);

  digitalWrite(led, LOW);
  digitalWrite(pinTemp, LOW);
  digitalWrite(pinHum, LOW);
  digitalWrite(pinRxTH, LOW);
  digitalWrite(pinRxD, LOW);

  Serial.println("Estación de Tierra lista.");
}

void loop() {
  // ---- Datos del satélite hacia el PC ----
  if (enlace.available() > 0) {
    digitalWrite(led, HIGH);

    String datos = enlace.readStringUntil('\n');
    datos.trim();

    if (datos.length() > 0) {
      // Miramos el tipo de mensaje (primer campo antes de ':')
      int fin = datos.indexOf(':');
      if (fin == -1) fin = datos.length();
      String scod = datos.substring(0, fin);

      // 1 y 5 -> temperatura/humedad
      if (scod == "1" || scod == "5") {
        digitalWrite(pinRxTH, HIGH);   // se queda en HIGH una vez haya llegado algo
      }
      // 3 -> distancia
      if (scod == "3") {
        digitalWrite(pinRxD, HIGH);
      }

      Serial.println(datos);  // el PC/Python lo ve
    }

    digitalWrite(led, LOW);
  }

  // ---- Comandos del PC (Python) hacia satélite o para activar pines ----
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd.length() > 0) {

      int fin = cmd.indexOf(':');
      if (fin == -1) fin = cmd.length();
      int codigo = cmd.substring(0, fin).toInt();

      if (codigo == 20) {
        // controlar pinTemp
        int valor = cmd.substring(fin + 1).toInt();
        if (valor == 1) {
          digitalWrite(pinTemp, HIGH);
          Serial.println("PIN 2 (TEMP) -> HIGH");
        } else {
          digitalWrite(pinTemp, LOW);
          Serial.println("PIN 2 (TEMP) -> LOW");
        }
      }
      else if (codigo == 21) {
        // controlar pinHum
        int valor = cmd.substring(fin + 1).toInt();
        if (valor == 1) {
          digitalWrite(pinHum, HIGH);
          Serial.println("PIN 3 (HUM) -> HIGH");
        } else {
          digitalWrite(pinHum, LOW);
          Serial.println("PIN 3 (HUM) -> LOW");
        }
      } else {
        // cualquier otro comando se reenvía al satélite
        enlace.println(cmd);
        Serial.print("Comando reenviado al emisor: ");
        Serial.println(cmd);
      }
    }
  }
}
