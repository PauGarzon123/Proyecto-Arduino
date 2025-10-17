#include <SoftwareSerial.h>
SoftwareSerial mySerial(10, 11); // RX, TX (azul, naranja)

unsigned long nextMillis = 500;
//Este codigo envia un mensaje a otro arduino. Si el otro tiene el mismo, lo intentará leer y si lo hace correctamente mostrará "Se ha recibido el mensaje: Envío" en su IDE
void setup() {
   Serial.begin(9600);
   Serial.println("Empezamos la recepción");
   mySerial.begin(9600);
}
void loop() {
   delay (3000);
   mySerial.print("Envio");
   Serial.print("Hago un envío");
   if (mySerial.available()) {
      String data = mySerial.readString();
      Serial.print("Se ha recibido el mensaje: ");
      Serial.print(data);
   }
}