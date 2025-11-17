#include <SoftwareSerial.h>

SoftwareSerial enlace(10, 11);

// LEDs
const int LED_ALARMA  = A1;
const int LED_RASTREO = A2;
const int LED_DIST    = A3;
const int LED_TH      = A4;
const int LED_ERROR   = A5;

void setup() {
  Serial.begin(9600);
  enlace.begin(9600);

  pinMode(LED_ALARMA, OUTPUT);
  pinMode(LED_RASTREO, OUTPUT);
  pinMode(LED_DIST, OUTPUT);
  pinMode(LED_TH, OUTPUT);
  pinMode(LED_ERROR, OUTPUT);

  Serial.println("Estación de Tierra lista.");
}

void loop() {

  if (enlace.available() > 0) {
    String datos = enlace.readStringUntil('\n');
    datos.trim();
    Serial.println(datos);

    // Temp/Hum
    if (datos.startsWith("1:")) {
      digitalWrite(LED_TH, HIGH); delay(20);
      digitalWrite(LED_TH, LOW);
    }

    // Distancia
    else if (datos.startsWith("3:")) {
      digitalWrite(LED_DIST, HIGH); delay(20);
      digitalWrite(LED_DIST, LOW);
    }

    // Errores
    else if (datos.startsWith("2:") || datos.startsWith("4:")) {
      digitalWrite(LED_ERROR, HIGH); delay(150);
      digitalWrite(LED_ERROR, LOW);
    }

    // Alarma
    else if (datos.startsWith("6:")) {
      digitalWrite(LED_ALARMA, HIGH); delay(400);
      digitalWrite(LED_ALARMA, LOW);
    }

    // Rastreo ON
    if (datos.indexOf("RASTREO") != -1)
      digitalWrite(LED_RASTREO, HIGH);

    // Ángulo fijo → rastreo OFF
    if (datos.indexOf("ANGULO FIJO") != -1)
      digitalWrite(LED_RASTREO, LOW);
  }

  // Reenvío comandos del PC al satélite
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    enlace.println(cmd);
  }
}