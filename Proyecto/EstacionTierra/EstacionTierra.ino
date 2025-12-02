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
const int LED_POS     = A0;

void setup() {

  // UART con el SATÉLITE
  Serial.begin(115200);

  // UART con el PC (FTDI USB-C)
  puertoPC.begin(115200);

  pinMode(LED_ALARMA, OUTPUT);
  pinMode(LED_RASTREO, OUTPUT);
  pinMode(LED_DIST, OUTPUT);
  pinMode(LED_TH, OUTPUT);
  pinMode(LED_ERROR, OUTPUT);
  pinMode(LED_POS, OUTPUT);

  puertoPC.println("Estación de Tierra lista (FTDI OK).");
}

void loop() {

  // ============================
  //  DATOS DESDE EL SATÉLITE
  // ============================
  if (Serial.available() > 0) {

    String datos = Serial.readStringUntil('\n');
    datos.trim();

    // REENVÍA AL PC (via FTDI)
    puertoPC.println(datos);

    // LEDS
    if (datos.startsWith("1:")) { 
      digitalWrite(LED_TH, HIGH);  delay(20); digitalWrite(LED_TH, LOW); 
    }
    else if (datos.startsWith("3:")) {
      digitalWrite(LED_DIST, HIGH);  delay(20); digitalWrite(LED_DIST, LOW);
    }
    else if (datos.startsWith("2:") ||
             datos.startsWith("4:") ||
             datos.startsWith("10:")) {
      digitalWrite(LED_ERROR, HIGH); delay(150); digitalWrite(LED_ERROR, LOW);
    }
    else if (datos.startsWith("6:")) {
      digitalWrite(LED_ALARMA, HIGH); delay(400); digitalWrite(LED_ALARMA, LOW);
    }
    else if (datos.startsWith("7:")) {
      digitalWrite(LED_RASTREO, HIGH);
    }
    else if (datos.startsWith("8:")) {
      digitalWrite(LED_RASTREO, LOW);
    }
    else if (datos.startsWith("9:")) {
      digitalWrite(LED_POS, HIGH); delay(20); digitalWrite(LED_POS, LOW);
    }
  }

}
