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
  //Leer los posibles mensajes que lleguen de la estación tierra
  //Extraer el codigo
  if (enlace.available() > 0) {
    String cmd = enlace.readStringUntil('\n');
    cmd.trim();
    int fin=cmd.indexOf(':',0); 
    int codigo = cmd.substring(0, fin).toInt(); 
    int inicio = fin+1;

  //Depende del codigo, hacer diferentes cosas
    if (codigo == 1) {
      transmitir = false;
      enlace.println("Transmisión detenida en emisor.");
    } 
    else if (codigo == 2) {
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
      enlace.print("1:");
      enlace.print(t);
      enlace.print(":");
      enlace.println(h);
      delay(200);
      digitalWrite(led1, LOW);
    }
  }

  // si pasan más de 7 segundos sin lectura  que indique fallo
  if (transmitir && (millis() - ultimoDatoOK > timeoutFallo)) {
    enlace.println("2:");
    ultimoDatoOK = millis();  // no enviar en bucle
  }
}
