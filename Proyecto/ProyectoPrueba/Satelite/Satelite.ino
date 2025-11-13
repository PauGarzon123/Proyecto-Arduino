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
bool transmitirTH   = true;   // enviar temperatura/humedad
bool transmitirDist = true;   // enviar distancia

// Medias en satélite o en tierra
bool mediasEnSatelite = true;   // true = se calculan aquí y se envían como código 5

// Tiempos
unsigned long ultimoDatoOKTempHum = 0;
unsigned long ultimoDatoOKdist    = 0;
const unsigned long timeoutFallo  = 7000;

unsigned long lastReadTH   = 0;      // temperatura / humedad
unsigned long lastReadDist = 0;      // distancia / radar

// Periodos (modificables desde tierra vía comandos 30 y 31)
unsigned long intervaloTH   = 1000;  // ms
unsigned long intervaloDist = 100;   // ms

// Servo / radar
int angulo       = 0;
int incremento   = 5;
bool modoRastreo = true;   // true = barrido continuo, false = ángulo fijo
int anguloFijo   = 90;     // por defecto

// Medias en satélite
int   contLecturaMedias = 0;
float sumaT = 0, sumaH = 0;

// Límites para alarma (solo para referencia; realmente el control lo hace Python)
float valorlimiteT = 1000;
float valorlimiteH = 1000;

void setup() {
  pinMode(led1, OUTPUT);
  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);

  enlace.begin(9600);
  dht.begin();
  servoMotor.attach(SERVO);

  enlace.println("Emisor listo. Esperando comandos...");
}

float medirDistancia() {
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);

  long duracion = pulseIn(ECHO, HIGH, 30000); // timeout 30 ms
  if (duracion == 0) {
    return NAN; // sin eco
  }
  float distancia = duracion * 0.0343 / 2.0;
  return distancia;
}

int moverServoBarrido() {
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

void procesarComandos() {
  if (!enlace.available()) return;

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
      if (nuevo >= 100) intervaloTH = nuevo;
      enlace.print("Nuevo intervaloTH: ");
      enlace.println(intervaloTH);
      break;
    }

    case 31: { // nuevo intervalo Distancia en ms
      String s = cmd.substring(inicio);
      unsigned long nuevo = s.toInt();
      if (nuevo >= 20) intervaloDist = nuevo;
      enlace.print("Nuevo intervaloDist: ");
      enlace.println(intervaloDist);
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
  if (transmitirTH && (ahora - lastReadTH >= intervaloTH)) {
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
  if (transmitirDist && (ahora - lastReadDist >= intervaloDist)) {
    lastReadDist = ahora;

    int angActual;
    if (modoRastreo) {
      angActual = moverServoBarrido();
    } else {
      aplicarServoOrientacionFija();
      angActual = anguloFijo;
    }

    float d = medirDistancia();
    if (!isnan(d)) {
      ultimoDatoOKdist = ahora;
      digitalWrite(led1, HIGH);

      enlace.print("3:");
      enlace.print(d);
      enlace.print(":");
      enlace.println(angActual);

      digitalWrite(led1, LOW);
    }
  }

  // ==== MENSAJES DE FALLO POR TIMEOUT ====
  if (transmitirTH && (ahora - ultimoDatoOKTempHum > timeoutFallo)) {
    enlace.println("2:");
    ultimoDatoOKTempHum = ahora;
  }

  if (transmitirDist && (ahora - ultimoDatoOKdist > timeoutFallo)) {
    enlace.println("4:");
    ultimoDatoOKdist = ahora;
  }
}
