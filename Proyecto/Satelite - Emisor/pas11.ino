#include <SoftwareSerial.h>
#include <DHT.h>

#define DHTPIN 3
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

SoftwareSerial enlace(10, 11);  // RX, TX (comunicación con receptor)
const int led1 = 13;
bool transmitir = true;
unsigned long lastRead = 0;

void setup() {
  pinMode(led1, OUTPUT);
  enlace.begin(9600);
  dht.begin();
  enlace.println("Emisor listo. Esperando comandos START/STOP...");
}

void loop() {
  // Escucha comandos del receptor
  if (enlace.available() > 0) {
    String cmd = enlace.readStringUntil('\n');
    cmd.trim();

    if (cmd.equalsIgnoreCase("STOP")) {
      transmitir = false;
      enlace.println("Transmisión detenida en emisor.");
    } 
    else if (cmd.equalsIgnoreCase("START")) {
      transmitir = true;
      enlace.println("Transmisión reanudada en emisor.");
    }
  }

  // Enviar datos
  if (transmitir && millis() - lastRead >= 3000) {
    lastRead = millis();
    float h = dht.readHumidity();
    float t = dht.readTemperature();

    if (!isnan(h) && !isnan(t)) {
      digitalWrite(led1, HIGH);
      enlace.print("T:");
      enlace.print(t);
      enlace.print(":");
      enlace.println(h);
      delay(500);
      digitalWrite(led1, LOW);
    }
  }
}
