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

// Periodos (modificables desde tierra vía comandos 30 y 31)
unsigned long periodoTH   = 1000;  // ms
unsigned long periodoDist = 100;   // ms

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

  String cmd = enlace.readStringUntil('\n');
  cmd.trim();
  if (cmd.length() == 0) return;

  int fin = cmd.indexOf(':');
  if (fin == -1) fin = cmd.length();
  int codigo = cmd.substring(0, fin).toInt();
  int inicio = fin + 1;

  switch (codigo) {
    case 1: // parar T/H
      transmitirTH = false;
      enlace.println("TH STOP");
      break;

    case 2: // reanudar T/H
      transmitirTH = true;
      enlace.println("TH START");
      break;

    case 3: // parar distancia
      transmitirDist = false;
      enlace.println("DIST STOP");
      break;

    case 4: // reanudar distancia
      transmitirDist = true;
      enlace.println("DIST START");
      break;

    case 10: // medias en satélite
      mediasEnSatelite = true;
      contLecturaMedias = 0;
      sumaT = 0;
      sumaH = 0;
      enlace.println("Medias en SATELITE");
      break;

    case 11: // medias en tierra
      mediasEnSatelite = false;
      contLecturaMedias = 0;
      sumaT = 0;
      sumaH = 0;
      enlace.println("Medias en TIERRA");
      break;

    case 12: { // valor límite T y H (no estrictamente necesario aquí, pero lo guardamos)
      int fin2 = cmd.indexOf(':', inicio);
      if (fin2 == -1) fin2 = cmd.length();
      String st = cmd.substring(inicio, fin2);
      String sh = cmd.substring(fin2 + 1);
      valorlimiteT = st.toFloat();
      valorlimiteH = sh.toFloat();
      enlace.println("Nuevos limites T/H recibidos.");
      break;
    }

    case 30: { // nuevo intervalo TH en ms
      String s = cmd.substring(inicio);
      unsigned long nuevo = s.toInt();
      if (nuevo >= 100) periodoTH = nuevo;
      enlace.print("Nuevo intervaloTH: ");
      enlace.println(periodoTH);
      break;
    }

    case 31: { // nuevo intervalo Distancia en ms
      String s = cmd.substring(inicio);
      unsigned long nuevo = s.toInt();
      if (nuevo >= 20) periodoDist = nuevo;
      enlace.print("Nuevo intervaloDist: ");
      enlace.println(periodoDist);
      break;
    }

    case 40: // modo rastreo
      modoRastreo = true;
      enlace.println("Modo RASTREO activado.");
      break;

    case 41: { // ángulo fijo
      String s = cmd.substring(inicio);
      anguloFijo = s.toInt();
      if (anguloFijo < 0)   anguloFijo = 0;
      if (anguloFijo > 180) anguloFijo = 180;
      modoRastreo = false;
      enlace.print("Modo ANGULO FIJO: ");
      enlace.println(anguloFijo);
      break;
    }

    default:
      // comando desconocido
      enlace.print("CMD desconocido: ");
      enlace.println(cmd);
      break;
  }
}

void loop() {
  unsigned long ahora = millis();

  // Procesar comandos desde la estación
  procesarComandos();

  // ==== TEMPERATURA / HUMEDAD ====
  if (transmitirTH && (ahora - lastReadTH >= periodoTH)) {
    lastReadTH = ahora;

    float h = dht.readHumidity();
    float t = dht.readTemperature();

    if (!isnan(h) && !isnan(t)) {
      ultimoDatoOKTempHum = ahora;
      digitalWrite(led1, HIGH);

      enlace.print("1:");
      enlace.print(t);
      enlace.print(":");
      enlace.println(h);

      digitalWrite(led1, LOW);

      if (mediasEnSatelite) {
        sumaT += t;
        sumaH += h;
        contLecturaMedias++;
        if (contLecturaMedias >= 10) {
          float tM = sumaT / 10.0;
          float hM = sumaH / 10.0;
          enlace.print("5:");
          enlace.print(tM);
          enlace.print(":");
          enlace.println(hM);
          contLecturaMedias = 0;
          sumaT = 0;
          sumaH = 0;
        }
      }
    }
    // si fallan, el código 2: lo gestiona más abajo por timeout
  }

  // ==== DISTANCIA / RADAR ====
  if (transmitirDist && (ahora - lastReadDist >= periodoDist)) {
    lastReadDist = ahora;

    int angActual;
    if (modoRastreo) {
      angActual = moverServoBarrido();

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
