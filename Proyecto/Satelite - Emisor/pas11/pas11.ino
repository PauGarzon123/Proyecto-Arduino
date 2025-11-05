#include <SoftwareSerial.h>
#include <DHT.h>

#define DHTPIN 3
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

SoftwareSerial enlace(10, 11);
const int led1 = 13;

bool transmitir = true;
unsigned long lastRead = 0; 
unsigned long ultimoDatoOK = 0;   
const unsigned long intervaloLectura = 3000;   // cada 3 s
const unsigned long timeoutFallo = 7000;      

void setup() {
  pinMode(led1, OUTPUT);
  enlace.begin(9600);
  dht.begin();
  enlace.println("Emisor listo. Esperando comandos START/STOP...");
}

void loop() {
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

  // lectura del sensor cada 3 segundos
  if (transmitir && millis() - lastRead >= intervaloLectura) {
    lastRead = millis();

    float h = dht.readHumidity();
    float t = dht.readTemperature();

    if (!isnan(h) && !isnan(t)) {
      ultimoDatoOK = millis();  
      digitalWrite(led1, HIGH);
      enlace.print("T:");
      enlace.print(t);
      enlace.print(":");
      enlace.println(h);
      delay(200);
      digitalWrite(led1, LOW);
    }
  }

  // si pasan más de 3 segundos sin lectura  que indique fallo
  if (transmitir && (millis() - ultimoDatoOK > timeoutFallo)) {
    enlace.println("Fallo");
    ultimoDatoOK = millis();  // no enviar en bucle
  }
}
