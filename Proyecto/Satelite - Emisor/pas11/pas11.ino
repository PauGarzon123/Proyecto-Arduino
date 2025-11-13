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

// Estados de transmisión
bool transmitirTH = true;
bool transmitirDist = true;

// Medias en satélite o en tierra
bool mediasEnSatelite = true;

// Tiempos
unsigned long lastReadTH = 0;
unsigned long lastReadDist = 0;
unsigned long ultimoDatoOKTempHum = 0;
unsigned long ultimoDatoOKdist = 0;
// Periodos
unsigned long intervaloTempHum = 300;
unsigned long intervaloDist = 100;
const unsigned long timeoutFallo = 7000;

// servo/radar
int angulo = 0;
int incremento = 5;  //la cantidad de angulo que avanza por bucle
bool modoRastreo = true;   // true = barrido continuo, false = ángulo fijo
int anguloFijo   = 90;     // por defecto

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
  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);
  enlace.begin(9600);
  dht.begin();
  servoMotor.attach(SERVO);
  enlace.println("Emisor listo. Esperando comandos START/STOP...");
}

/////////////////////// FUNCIONES //////////////////////
void procesarComando(String cmd) {
  cmd.trim();
  int fin = cmd.indexOf(':');
  int codigo = cmd.substring(0, fin).toInt();
  int inicio = fin + 1;

  if (codigo == 1) {  
    transmitirTH = false;
    enlace.println("TH STOP");
  } 
  else if (codigo == 2) {  
    transmitirTH = true;
    enlace.println("TH START");
  } 
  else if (codigo == 3) {  
    transmitirDist = false;
    enlace.println("DIST STOP");
  } 
  else if (codigo == 4) {  
    transmitirDist = true;
    enlace.println("DIST START");
  } 
  else if (codigo == 5) {  
    String s = cmd.substring(inicio);
    unsigned long nuevo = s.toInt();
    if (nuevo >= 100) intervaloTempHum = nuevo;
    enlace.print("Nuevo intervaloTempHum: ");
    enlace.println(intervaloTempHum);
  } 
  else if (codigo == 6) {  
    String s = cmd.substring(inicio);
    unsigned long nuevo = s.toInt();
    if (nuevo >= 20) intervaloDist = nuevo;
    enlace.print("Nuevo intervaloDist: ");
    enlace.println(intervaloDist);
  } 
  else if (codigo == 7) {  
    modoRastreo = true;
    enlace.println("Modo RASTREO activado.");
  } 
  else if (codigo == 8) {  
    String s = cmd.substring(inicio);
    anguloFijo = s.toInt();
    if (anguloFijo < 0)   anguloFijo = 0;
    if (anguloFijo > 180) anguloFijo = 180;
    modoRastreo = false;
    enlace.print("Modo ANGULO FIJO: ");
    enlace.println(anguloFijo);
  } 
  else if (codigo == 10) {  
    mediasEnSatelite = true;
    contLecturaMedias = 0;
    sumaT = 0;
    sumaH = 0;
    enlace.println("Medias en SATELITE");
  } 
  else if (codigo == 11) {  
    mediasEnSatelite = false;
    contLecturaMedias = 0;
    sumaT = 0;
    sumaH = 0;
    enlace.println("Medias en TIERRA");
  } 
  else if (codigo == 12) {  
    int fin2 = cmd.indexOf(':', inicio);
    if (fin2 == -1) fin2 = cmd.length();
    String st = cmd.substring(inicio, fin2);
    String sh = cmd.substring(fin2 + 1);
    valorlimiteT = st.toFloat();
    valorlimiteH = sh.toFloat();
    enlace.println("Nuevos limites T/H recibidos.");
  } 
  else {  
    enlace.print("CMD desconocido: ");
    enlace.println(cmd);
  }
} 

void leerDistancia() {
  int ang;
  if (modoRastreo) ang = moverServo();
  else { aplicarServoOrientacionFija(); ang = anguloFijo; }

  float d = medirDistancia();
  if (isnan(d)) return;

  ultimoDatoOKdist = millis();
  enviarDistancia(d, ang);
}

float medirDistancia() {
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);
  long duracion = pulseIn(ECHO, HIGH, 30000);  // timeout de 30 ms
  if (duracion == 0) {
    return NAN;  // sin eco
  }
  float distancia = duracion * 0.0343 / 2;
  return distancia;
}

int moverServo() {
  servoMotor.write(angulo);
  delay(10);  // pequeño tiempo para estabilizar

  angulo += incremento;
  if (angulo >= 180 || angulo <= 0) incremento = -incremento;

  return angulo;
}

void aplicarServoOrientacionFija() {
  servoMotor.write(anguloFijo);
  delay(10);
}

void leerTemperaturaHumedad() {
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  if (isnan(h) || isnan(t)) return;

  ultimoDatoOKTempHum = millis();
  enviarTemperatura(t, h);
  calcularEnviarMedias(t, h);
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
  if (!mediasEnSatelite) return;

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
    if (mediaT >= valorlimiteT) {
      jT++;
      if (jT >= 3) enlace.println("6:");
    } else jT = 0;

    if (mediaH >= valorlimiteH) {
      jH++;
      if (jH >= 3) enlace.println("6:");
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
  if (transmitirTH && (millis() - ultimoDatoOKTempHum > timeoutFallo)) {
    enlace.println("2:");
    ultimoDatoOKTempHum = millis();
  }
  if (transmitirDist && (millis() - ultimoDatoOKdist > timeoutFallo)) {
    enlace.println("4:");
    ultimoDatoOKdist = millis();
  }
}

////////////////BUCLE//////////////////////
void loop() {
  unsigned long ahora = millis();
  if (enlace.available() > 0) {
    String cmd = enlace.readStringUntil('\n');
    procesarComando(cmd);
  }
  // Lectura independiente de cada sensor
  if (transmitirTH && (ahora - lastReadTH >= intervaloTempHum)) {
    lastReadTH = ahora;
    leerTemperaturaHumedad();
  }
  if (transmitirDist && (ahora - lastReadDist >= intervaloDist)) {
    lastReadDist = ahora;
    leerDistancia();
  }
  verificarTimeout();
}
