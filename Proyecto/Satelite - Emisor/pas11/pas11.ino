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
unsigned long periodoTempHum = 300;
unsigned long periodoDist = 100;
const unsigned long timeoutFallo = 7000;

// servo/radar
int angulo = 0;
int incremento = 5;  //la cantidad de angulo que avanza por bucle
bool modoRastreo = true;   // true = barrido continuo, false = ángulo fijo
int anguloFijo   = 90;     // por defecto

// Variables para medias
const int N = 10;
float tempCola[N];
float humCola[N];
int idx = 0;
int cont = 0;
int nuevos = 0;
int jT = 0;
int jH = 0;
float mediaT = 0;
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
    if (nuevo >= 100) periodoTempHum = nuevo;
    enlace.print("Nuevo periodoTempHum: ");
    enlace.println(periodoTempHum);
  } 
  else if (codigo == 6) {  
    String s = cmd.substring(inicio);
    unsigned long nuevo = s.toInt();
    if (nuevo >= 20) periodoDist = nuevo;
    enlace.print("Nuevo PeriodoDist: ");
    enlace.println(periodoDist);
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
    enlace.println("Medias en SATELITE");
  } 
  else if (codigo == 11) {  
    mediasEnSatelite = false;
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

    // --- actualizar cola circular ---
    tempCola[idx] = t;
    humCola[idx] = h;
    idx = (idx + 1) % N;
    if (cont < N) cont++;

    nuevos++;


    // --- enviar medias solo cuando hay 10 valores ---
    if (cont == N && nuevos == N) {
        // --- calcular medias ---
        float sumaT = 0, sumaH = 0;
        for (int i = 0; i < cont; i++) {
            sumaT += tempCola[i];
            sumaH += humCola[i];
        }
        mediaT = sumaT / cont;
        mediaH = sumaH / cont;
      
        enlace.print("5:");
        enlace.print(mediaT);
        enlace.print(":");
        enlace.println(mediaH);

        nuevos = 0;

        // alarmas igual que antes
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
  if (enlace.available() > 0) {
    String cmd = enlace.readStringUntil('\n');
    procesarComando(cmd);
  }
  // Lectura independiente de cada sensor
  if (transmitirTH &&  millis() - lastReadTH >= periodoTempHum) {
    lastReadTH = millis();
    leerTemperaturaHumedad();
  }
  if (transmitirDist &&  millis() - lastReadDist >= periodoDist) {
    lastReadDist = millis();
    leerDistancia();
  }
  verificarTimeout();
}
