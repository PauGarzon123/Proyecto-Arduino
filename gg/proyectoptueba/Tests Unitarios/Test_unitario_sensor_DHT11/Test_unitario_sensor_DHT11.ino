#include <SoftwareSerial.h>
#include <DHT.h>
#define DHTPIN 2
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);


void setup() {

   Serial.begin(9600);
   // Inicialización del sensor
   dht.begin();
}

void loop() {
   delay(3000);
   float h = dht.readHumidity();
   float t = dht.readTemperature();
   if (isnan(h) || isnan(t)){ 
      Serial.println("Error a leer el sensor DHT11");
   }
   else {
      Serial.println("El sensor da datos correctos");

   }

}