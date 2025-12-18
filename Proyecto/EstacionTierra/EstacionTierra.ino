#include <SoftwareSerial.h>

// UART secundaria → FTDI USB-C
// Pin 8 = RX (recibe del FTDI TXD)
// Pin 9 = TX (envía al FTDI RXD)
SoftwareSerial puertoPC(8, 9);  

// LEDs
const int LED_ALARMA  = A1;
const int LED_RASTREO = A2;
const int LED_DIST    = A3;
const int LED_TH      = A4;
const int LED_ERROR   = A5;

void setup() {

  // UART con el SATÉLITE
  Serial.begin(9600);

  // UART con el PC (FTDI USB-C)
  puertoPC.begin(9600);

  pinMode(LED_ALARMA, OUTPUT);
  pinMode(LED_RASTREO, OUTPUT);
  pinMode(LED_DIST, OUTPUT);
  pinMode(LED_TH, OUTPUT);
  pinMode(LED_ERROR, OUTPUT);

  puertoPC.println("Estación de Tierra lista (FTDI OK).");
}

void loop() {

  // ============================
  // 1) DATOS DESDE EL SATÉLITE
  // ============================
  if (Serial.available()) {
    String datos = Serial.readStringUntil('\n');
    datos.trim();

    puertoPC.println(datos);

    if (datos.startsWith("1:")) { // led datos Temp/hum
      digitalWrite(LED_TH, HIGH); delay(20); digitalWrite(LED_TH, LOW); 
    }
    else if (datos.startsWith("3:")) {//led datos dist
      digitalWrite(LED_DIST, HIGH); delay(20); digitalWrite(LED_DIST, LOW);
    }
    else if (datos.startsWith("2:") ||
             datos.startsWith("4:") ||
             datos.startsWith("10:")) {//leds error temp,hum,satelite
      digitalWrite(LED_ERROR, HIGH); delay(150); digitalWrite(LED_ERROR, LOW);
    }
    else if (datos.startsWith("6:")) {//error medias
      digitalWrite(LED_ALARMA, HIGH); delay(400); digitalWrite(LED_ALARMA, LOW);
    }
  }

  // ============================
  // 2) DATOS DESDE EL PC (FTDI)
  // ============================
  if (puertoPC.available()) {
    String comando = puertoPC.readStringUntil('\n');
    comando.trim();

    Serial.println(comando);

    if (comando.startsWith("7:")) {//led modo rastreo
      digitalWrite(LED_RASTREO, HIGH);
    }
    else if (comando.startsWith("8:")) {//fin modo rastreo
      digitalWrite(LED_RASTREO, LOW);
    }
  }
}


