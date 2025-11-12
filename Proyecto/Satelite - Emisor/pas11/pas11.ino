#include <SoftwareSerial.h>
#include <DHT.h>
#include <Servo.h>

#define DHTPIN 3
#define DHTTYPE DHT11
#define TRIG 4
#define ECHO 5
#define SERVO 6
DHT dht(DHTPIN, DHTTYPE);
Servo servoMotor;
SoftwareSerial enlace(10, 11);
const int led1 = 13;

// Variables de estado
bool transmitir = true;
bool hacermedias = true;
unsigned long lastRead = 0; 
unsigned long ultimoDatoOKTempHum = 0;
unsigned long ultimoDatoOKdist = 0;
unsigned long ultimoDatoOKang = 0;
const unsigned long intervaloLectura = 300;   // cada 3 s
const unsigned long timeoutFallo = 7000;

// Variables de servo
int angulo = 0;
int incremento = 5; //la cantidad de angulo que avanza por bucle   

// Variables para medias
int contLecturaMedias = 0;
int jT = 0;
int jH = 0;
float sumaT = 0;
float mediaT = 0;
float sumaH = 0;
float mediaH = 0;
float valorlimiteT = 100;
float valorlimiteH = 100;

void setup() {
  pinMode(led1, OUTPUT);
  pinMode(TRIG,OUTPUT);
  pinMode(ECHO,INPUT);
  enlace.begin(9600);
  dht.begin();
  servoMotor.attach(SERVO);
  enlace.println("Emisor listo. Esperando comandos START/STOP...");
}

/////////////////////// FUNCIONES //////////////////////
void procesarComando(String cmd) {
  cmd.trim();
  int fin = cmd.indexOf(':', 0);
  int codigo = cmd.substring(0, fin).toInt();
  int inicio = fin + 1;

  if(codigo == 1){
    transmitir = false;
    enlace.println("Transmisión detenida en emisor.");
  }
  else if(codigo == 2){
    transmitir = true;
    enlace.println("Transmisión reanudada en emisor.");
  }
  else if(codigo == 10){
    hacermedias = true;
  }
  else if(codigo == 11){
    hacermedias = false;
    sumaT = sumaH = 0;
    contLecturaMedias = 0;
    mediaT = mediaH = 0;
  }
  else if(codigo == 12){
    fin = cmd.indexOf(':', inicio);
    valorlimiteT = cmd.substring(inicio, fin).toFloat();
    inicio = fin + 1;
    valorlimiteH = cmd.substring(inicio).toFloat();
  }
}
float medirDistancia() {
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);
  long duracion  = pulseIn(ECHO, HIGH, 30000); // timeout de 30 ms
  if (duracion == 0) {
    return NAN; // sin eco
  }
  float distancia = duracion * 0.0343 / 2;
  return distancia;
}

int moverServo() {
  servoMotor.write(angulo);
  delay(20);  // pequeño tiempo para estabilizar

  angulo += incremento;
  if (angulo >= 180 || angulo <= 0) incremento = -incremento;

  return angulo;
}

void leerSensores() {
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  float d = medirDistancia();
  int ang = moverServo();

  if(!isnan(h) && !isnan(t)) {
    ultimoDatoOKTempHum = millis();
    enviarTemperatura(t, h);
    calcularEnviarMedias(t, h);
  }

  if(!isnan(d)) {
    ultimoDatoOKdist = millis();
    enviarDistancia(d, ang);
  }
}

void enviarTemperatura(float t, float h) {
  digitalWrite(led1, HIGH);
  enlace.print("1:");
  enlace.print(t);
  enlace.print(":");
  enlace.println(h);
  delay(50);
  digitalWrite(led1, LOW);
}

void calcularEnviarMedias(float t, float h) {
  if (!hacermedias) return;

  sumaT += t;
  sumaH += h;
  contLecturaMedias++;

  if (contLecturaMedias >= 10) {
    mediaT = sumaT / 10;
    mediaH = sumaH / 10;
    enlace.print("5:");
    enlace.print(mediaT);
    enlace.print(":");
    enlace.println(mediaH);

    contLecturaMedias = 0;
    sumaT = sumaH = 0;

    // Verificar si hay 3 medias consecutivas por encima de límites
    if(mediaT >= valorlimiteT) {
      jT++;
      if(jT >= 3) enlace.println("6:");
    } else jT = 0;

    if(mediaH >= valorlimiteH) {
      jH++;
      if(jH >= 3) enlace.println("6:");
    } else jH = 0;
  }
}

void enviarDistancia(float d, int ang) {
  digitalWrite(led1, HIGH);
  enlace.print("3:");
  enlace.print(d);
  enlace.print(":");
  enlace.println(ang);
  delay(50);
  digitalWrite(led1, LOW);
}

void verificarTimeout() {
  if(transmitir && (millis() - ultimoDatoOKTempHum > timeoutFallo)) {
    enlace.println("2:");
    ultimoDatoOKTempHum = millis();
  }
  if(transmitir && (millis() - ultimoDatoOKdist > timeoutFallo)) {
    enlace.println("4:");
    ultimoDatoOKdist = millis();
  }
}

////////////////BUCLE//////////////////////
void loop() {
  //Revisar comandos entrantes
  if(enlace.available() > 0){
    String cmd = enlace.readStringUntil('\n');
    procesarComando(cmd);
  }
  // lectura del sensores
  if (transmitir && millis() - lastRead >= intervaloLectura) {
    lastRead = millis();
    leerSensores();
  }
  verificarTimeout();
}


