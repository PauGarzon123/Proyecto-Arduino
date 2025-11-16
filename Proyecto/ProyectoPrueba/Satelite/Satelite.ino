#include <SoftwareSerial.h>
#include <DHT.h>
#include <Servo.h>

#define DHTPIN 6
#define DHTTYPE DHT11
#define TRIG 4
#define ECHO 5
#define SERVO 3

DHT dht(DHTPIN, DHTTYPE);
Servo servoMotor;
SoftwareSerial enlace(10, 11);  // comunicación con la Estación

const int led1 = 13;

// Estados de transmisión
bool transmitirTH = true;
bool transmitirDist = true;

// Medias en satélite o tierra
bool mediasEnSatelite = true;

// Tiempos
unsigned long lastReadTH = 0;
unsigned long lastReadDist = 0;
unsigned long ultimoDatoOKTempHum = 0;
unsigned long ultimoDatoOKdist = 0;

unsigned long intervaloTempHum = 300;
unsigned long intervaloDist = 100;
const unsigned long timeoutFallo = 7000;

// SERVO
bool modoRastreo = false;   // 🚫 NO se mueve al inicio
int incremento = 5;
int angulo = 0;
int anguloFijo = 90;

// medias
int contLecturaMedias = 0;
float sumaT = 0, sumaH = 0;
float valorlimiteT = 100, valorlimiteH = 100;

void setup() {
  pinMode(led1, OUTPUT);
  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);

  enlace.begin(9600);
  dht.begin();
  servoMotor.attach(SERVO);

  enlace.println("Satélite listo.");
}

void procesarComando(String cmd) {
  cmd.trim();
  int fin = cmd.indexOf(':');
  int codigo = cmd.substring(0, fin).toInt();
  int inicio = fin + 1;

  if (codigo == 1) transmitirTH = false;
  else if (codigo == 2) transmitirTH = true;
  else if (codigo == 3) transmitirDist = false;
  else if (codigo == 4) transmitirDist = true;
  else if (codigo == 5) intervaloTempHum = cmd.substring(inicio).toInt();
  else if (codigo == 6) intervaloDist = cmd.substring(inicio).toInt();
  else if (codigo == 7) { modoRastreo = true; enlace.println("Modo RASTREO activado."); }
  else if (codigo == 8) {
      anguloFijo = cmd.substring(inicio).toInt();
      if (anguloFijo < 0) anguloFijo = 0;
      if (anguloFijo > 180) anguloFijo = 180;
      modoRastreo = false;
      enlace.println("Modo ANGULO FIJO activado.");
  }
  else if (codigo == 10) {
      mediasEnSatelite = true;
      sumaT = sumaH = 0;
      contLecturaMedias = 0;
  }
  else if (codigo == 11) {
      mediasEnSatelite = false;
      sumaT = sumaH = 0;
      contLecturaMedias = 0;
  }
  else if (codigo == 12) {
      int pos = cmd.indexOf(':', inicio);
      valorlimiteT = cmd.substring(inicio, pos).toFloat();
      valorlimiteH = cmd.substring(pos+1).toFloat();
  }
}

float medirDistancia() {
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);
  long duracion = pulseIn(ECHO, HIGH, 30000);
  if (duracion == 0) return NAN;
  return duracion * 0.0343 / 2;
}

int moverServo() {
  servoMotor.write(angulo);
  delay(10);
  angulo += incremento;
  if (angulo >= 180 || angulo <= 0) incremento = -incremento;
  return angulo;
}

void aplicarServoFijo() {
  servoMotor.write(anguloFijo);
  delay(10);
}

void enviarTempHum(float t, float h) {
  enlace.print("1:");
  enlace.print(t);
  enlace.print(":");
  enlace.println(h);
}

void enviarDist(float d, int ang) {
  enlace.print("3:");
  enlace.print(d);
  enlace.print(":");
  enlace.println(ang);
}

void loop() {
  if (enlace.available() > 0) {
    String cmd = enlace.readStringUntil('\n');
    procesarComando(cmd);
  }

  // TEMP/HUM
  if (transmitirTH && millis() - lastReadTH >= intervaloTempHum) {
    lastReadTH = millis();
    float h = dht.readHumidity();
    float t = dht.readTemperature();
    if (!isnan(t) && !isnan(h)) {
      ultimoDatoOKTempHum = millis();
      enviarTempHum(t,h);
    } else {
      enlace.println("2:");
    }
  }

  // DISTANCIA
  if (transmitirDist && millis() - lastReadDist >= intervaloDist) {
    lastReadDist = millis();

    int ang;
    if (modoRastreo) ang = moverServo();
    else { aplicarServoFijo(); ang = anguloFijo; }

    float d = medirDistancia();
    if (!isnan(d)) {
      ultimoDatoOKdist = millis();
      enviarDist(d,ang);
    }
    else enlace.println("4:");
  }

  // TIMEOUTS
  if (millis() - ultimoDatoOKTempHum > timeoutFallo)
    enlace.println("2:");
  if (millis() - ultimoDatoOKdist > timeoutFallo)
    enlace.println("4:");
}
