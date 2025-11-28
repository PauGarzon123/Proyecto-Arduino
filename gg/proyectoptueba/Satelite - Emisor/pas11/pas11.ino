#include <SoftwareSerial.h>   // Librería para usar RX/TX en pines diferentes del 0 y 1
#include <DHT.h>              // Librería del sensor de temperatura/humedad DHT
#include <Servo.h>            // Librería para controlar el servo

// ------------ DEFINICIÓN DE PINES DEL SATÉLITE ------------
#define DHTPIN 6      // Pin donde conectamos el sensor DHT11
#define DHTTYPE DHT11 // Tipo de sensor DHT
#define TRIG 4        // Pin TRIG del sensor de distancia
#define ECHO 5        // Pin ECHO del sensor de distancia
#define SERVO 3       // Pin donde está conectado el servo

DHT dht(DHTPIN, DHTTYPE);   // Instanciamos el sensor DHT
Servo servoMotor;           // Instancia para controlar el servo
SoftwareSerial enlace(10, 11);  // Comunicación con la estación tierra
const int led1 = 13;        // LED que usarás para indicar envío de datos


// ------------ ESTADOS DE TRANSMISIÓN ------------
bool transmitirTH = true;   // ¿Se está enviando temperatura/humedad?
bool transmitirDist = true; // ¿Se está enviando distancia?
bool transmitirPos = true;  // ¿Se está enviando posición orbital?


// ------------ CÁLCULO DE MEDIAS ------------
bool mediasEnSatelite = true; // True = medias aquí; False = medias en tierra


// ------------ TIMERS PARA CONTROLAR FRECUENCIA DE ENVÍO ------------
unsigned long lastReadTH = 0;    // Última lectura temp/hum
unsigned long lastReadDist = 0;  // Última lectura distancia
unsigned long lastReadPos = 0;   // Última lectura posición

unsigned long ultimoDatoOKTempHum = 0; // Momento del último dato correcto TH
unsigned long ultimoDatoOKdist = 0;    // Momento del último dato correcto Dist
unsigned long ultimoDatoOKPos = 0;     // Momento del último dato correcto Pos

// ------------ PERIODOS (modificables desde Python) ------------
unsigned long periodoTempHum = 300;  // Tiempo entre lecturas T/H
unsigned long periodoDist = 100;     // Tiempo entre lecturas distancia
unsigned long periodoPos = 500;      // Tiempo entre actualizaciones posición

const unsigned long timeoutFallo = 7000; // Si pasan 7s sin datos = ERROR


// ------------ VARIABLES DEL SERVO (RADAR) ------------
int angulo = 0;           // Ángulo actual del servo
int incremento = 5;       // Aumenta 5 grados por ciclo → barrido suave
bool modoRastreo = true;  // true = barrido autonómico; false = ángulo fijo
int anguloFijo = 90;      // Ángulo fijo por defecto (si se desactiva el rastreo)


// ------------ VARIABLES PARA CÁLCULO DE MEDIAS ------------
const int N = 10;          // Número de muestras necesarias para media
float tempCola[N];         // Cola circular temperatura
float humCola[N];          // Cola circular humedad

int idx = 0;               // Índice actual dentro de la cola circular
int cont = 0;              // Cuántos valores válidos llevamos
int nuevos = 0;            // Cuenta cuántos nuevos para decidir cuando enviar media

int jT = 0;                // Contador para detectar "tres medias seguidas malas" → alarma
int jH = 0;

float mediaT = 0;          // Media actual T
float mediaH = 0;          // Media actual H

float valorlimiteT = 100;  // Temperatura límite (modificable desde Python)
float valorlimiteH = 100;  // Humedad límite


// ------------ CONSTANTES PARA ÓRBITA ARTIFICIAL ------------
const double G = 6.67430e-11;          // Constante gravitacional
const double M = 5.97219e24;           // Masa de la Tierra (kg)
const double R_EARTH = 6371000;        // Radio de la Tierra (m)
const double ALTITUDE = 400000;        // Altura del satélite sobre superficie (m)

const double EARTH_ROTATION_RATE = 7.2921159e-5; // Velocidad rotación Tierra
const unsigned long MILLIS_BETWEEN_UPDATES = 1000;
const double TIME_COMPRESSION = 90.0;  // Factor de velocidad de órbita

// ------------ VARIABLES ORBITA ------------
unsigned long nextUpdate;   // Próxima actualización de posición
double real_orbital_period; // Periodo real de una órbita completa
double r;                   // Distancia desde centro de la Tierra


// ========================================================
// ====================== SETUP ===========================
// ========================================================
void setup() {

  pinMode(led1, OUTPUT);   // LED indicador de TX
  pinMode(TRIG, OUTPUT);   // Pin TRIG sensor distancia
  pinMode(ECHO, INPUT);    // Pin ECHO sensor distancia

  enlace.begin(9600);      // Comunicación con estación tierra
  dht.begin();             // Arrancamos sensor DHT
  servoMotor.attach(SERVO); // Servo listo

  // Valores iniciales para simulación orbital
  nextUpdate = MILLIS_BETWEEN_UPDATES;
  r = R_EARTH + ALTITUDE;

  // Fórmula del periodo orbital (ley de Kepler)
  real_orbital_period = 2 * PI * sqrt(pow(r, 3) / (G * M));

  enlace.println("Emisor listo. Esperando comandos START/STOP...");
}
//////////////////////////////////////////////////////////////
// ====================== PROCESAR COMANDO ==================
//////////////////////////////////////////////////////////////

void procesarComando(String cmd) {
  // Esta función recibe un mensaje desde Python.
  // El formato SIEMPRE es así:
  //
  //   "CODIGO:param1:param2|CHECKSUM"
  //
  // Ejemplos reales:
  //   "1:|107"
  //   "5:300|151"
  //   "12:40:80|XXX"
  //
  // Aquí:
  // 1. Comprobamos el checksum (para detectar errores en transmisión)
  // 2. Ejecutamos la acción correspondiente al código recibido

  cmd.trim(); // Quitamos espacios y saltos basura

  // ========= SEPARAR mensaje del checksum =========
  int sep = cmd.indexOf('|');
  String mensaje = cmd.substring(0, sep);       // lo anterior al "|"
  String strChecksum = cmd.substring(sep + 1);  // lo posterior

  int checksumRecibido = strChecksum.toInt();
  char buffer[120];
  mensaje.toCharArray(buffer, 120);
  int checksumCalculado = hacerChecksum(buffer);

  // ========= VERIFICAR CHECKSUM =========
  if (checksumCalculado != checksumRecibido) {
    // Si algo no cuadra, avisamos y no ejecutamos nada
    enlace.print("ERROR: Checksum no coincide.");
    return;
  }

  // ========= EXTRAEMOS EL CÓDIGO =========
  int fin = mensaje.indexOf(':');
  int codigo = mensaje.substring(0, fin).toInt();
  int inicio = fin + 1;


  //////////////////////////////////////////////////////
  // ============= SWITCH DE COMANDOS =================
  //////////////////////////////////////////////////////

  if (codigo == 1) {  
    // STOP temperatura/humedad
    transmitirTH = false;
    enlace.println("TH STOP");
  }

  else if (codigo == 2) {
    // START temperatura/humedad
    transmitirTH = true;
    enlace.println("TH START");
  }

  else if (codigo == 3) {
    // STOP distancia
    transmitirDist = false;
    enlace.println("DIST STOP");
  }

  else if (codigo == 4) {
    // START distancia
    transmitirDist = true;
    enlace.println("DIST START");
  }

  else if (codigo == 5) {
    // Cambiar periodo de T/H
    String s = mensaje.substring(inicio);
    unsigned long nuevo = s.toInt();

    if (nuevo >= 100) periodoTempHum = nuevo;

    enlace.print("Nuevo periodoTempHum: ");
    enlace.println(periodoTempHum);
  }

  else if (codigo == 6) {
    // Cambiar periodo de distancia
    String s = mensaje.substring(inicio);
    unsigned long nuevo = s.toInt();

    if (nuevo >= 20) periodoDist = nuevo;

    enlace.print("Nuevo PeriodoDist: ");
    enlace.println(periodoDist);
  }

  else if (codigo == 7) {
    // Activa modo rastreo del servo (escaneo automático)
    modoRastreo = true;
    enlace.println("Modo RASTREO activado.");
  }

  else if (codigo == 8) {
    // Poner ángulo fijo del servo (desactiva el rastreo automático)
    String s = mensaje.substring(inicio);
    anguloFijo = s.toInt();

    if (anguloFijo < 0) anguloFijo = 0;
    if (anguloFijo > 180) anguloFijo = 180;

    modoRastreo = false;

    enlace.print("Modo ANGULO FIJO: ");
    enlace.println(anguloFijo);
  }

  else if (codigo == 10) {
    // Las medias se calculan en el satélite
    mediasEnSatelite = true;
    enlace.println("Medias en SATELITE");
  }

  else if (codigo == 11) {
    // Las medias se calculan en la tierra (PC)
    mediasEnSatelite = false;
    enlace.println("Medias en TIERRA");
  }

  else if (codigo == 12) {
    // Cambiar límites máximos T y H
    int fin2 = mensaje.indexOf(':', inicio);

    if (fin2 == -1) fin2 = mensaje.length();

    String st = mensaje.substring(inicio, fin2);
    String sh = mensaje.substring(fin2 + 1);

    valorlimiteT = st.toFloat();
    valorlimiteH = sh.toFloat();

    enlace.println("Nuevos limites T/H recibidos.");
  }

  else {
    // Comando no reconocido
    enlace.print("CMD desconocido: ");
    enlace.println(cmd);
  }
}
//////////////////////////////////////////////////////////////
// ======================= MEDIR DISTANCIA =================
//////////////////////////////////////////////////////////////

void leerDistancia() {
  int ang;

  // Si estamos en modo rastreo → el servo se mueve solo
  if (modoRastreo)
      ang = moverServo();  // mueve servo 5° cada ciclo
  else {
      // Si NO estamos en rastreo → usamos el ángulo fijo enviado por el usuario
      aplicarServoOrientacionFija();
      ang = anguloFijo;
  }

  float d = medirDistancia();  // medimos distancia real con el HC-SR04

  if (isnan(d)) return;  // si no hay eco → no enviamos nada

  ultimoDatoOKdist = millis(); // guardamos "validación" de lectura correcta

  enviarDistancia(d, ang); // Enviamos al PC el ángulo y la distancia
}


float medirDistancia() {
  // El típico protocolo del HC-SR04:

  digitalWrite(TRIG, LOW);      // aseguramos pulso limpio
  delayMicroseconds(2);

  digitalWrite(TRIG, HIGH);     // pulso de disparo de 10us
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);

  // Esperamos eco. Si tarda más de 30ms abortamos → objeto demasiado lejos
  long duracion = pulseIn(ECHO, HIGH, 30000);

  if (duracion == 0) {
    // Si falló ecos → devolvemos NaN para que la función superior ignore
    return NAN;
  }

  // Fórmula del HC-SR04
  float distancia = duracion * 0.0343 / 2;

  return distancia;
}

void enviarDistancia(float d, int ang) {
  digitalWrite(led1, HIGH);

  char mensaje[50];
  // Formato: 3:distancia:angulo
  sprintf(mensaje, "3:%.2f:%d", d, ang);

  int checksum = hacerChecksum(mensaje);

  enlace.print(mensaje);
  enlace.print("|");
  enlace.println(checksum);

  delay(50);
  digitalWrite(led1, LOW);
}

//////////////////////////////////////////////////////////////
// ======================= SERVO RADAR ======================
//////////////////////////////////////////////////////////////

int moverServo() {
  // Escribimos el ángulo actual al servo
  servoMotor.write(angulo);
  delay(10);  // pequeña espera para evitar brincos (espasmos)

  // Ahora lo actualizamos para el siguiente ciclo
  angulo += incremento;

  // Si llega a 0° o 180° → invertimos el movimiento (rebote)
  if (angulo >= 180 || angulo <= 0)
      incremento = -incremento;

  return angulo;  // devolvemos el ángulo usado
}


void aplicarServoOrientacionFija() {
  // Cuando el usuario manda un ángulo fijo desde Python (8:valor)
  servoMotor.write(anguloFijo);
  delay(10);
}



//////////////////////////////////////////////////////////////
// ============ LEER TEMPERATURA Y HUMEDAD ==================
//////////////////////////////////////////////////////////////

void leerTemperaturaHumedad() {
  float h = dht.readHumidity();
  float t = dht.readTemperature();

  // Si el sensor falla → devolvemos NAN
  if (isnan(h) || isnan(t)) return;

  ultimoDatoOKTempHum = millis(); // marcamos lectura correcta

  enviarTemperatura(t, h);        // enviamos temp y hum al PC
  calcularEnviarMedias(t, h);     // si toca, calculamos medias
}



//////////////////////////////////////////////////////////////
// ======================== CHECKSUM =========================
//////////////////////////////////////////////////////////////

int hacerChecksum(char cadenaf[]){
    // Esta función hace LO MISMO que en Python:
    // sumamos todos los caracteres y hacemos mod 256
    int iC = 0;
    int suma = 0;
    while (iC < strlen(cadenaf)) {
        suma = suma + cadenaf[iC];
        iC++;
    }
    int checknum = suma % 256;
    return checknum;
}



//////////////////////////////////////////////////////////////
// =================== ENVÍO DE TEMPERATURA =================
//////////////////////////////////////////////////////////////

void enviarTemperatura(float t, float h) {
  digitalWrite(led1, HIGH);  // Encendemos LED 13 para indicar TX

  char mensaje[50];
  // Formato: 1:TEMP:HUM
  sprintf(mensaje, "1:%.2f:%.2f", t, h);

  int checksum = hacerChecksum(mensaje);

  // Enviamos mensaje + '|' + checksum
  enlace.print(mensaje);
  enlace.print("|");
  enlace.println(checksum);

  delay(50);
  digitalWrite(led1, LOW);
}



//////////////////////////////////////////////////////////////
// ================= ENVÍO DE MEDIAS =========================
//////////////////////////////////////////////////////////////

void calcularEnviarMedias(float t, float h) {

    // Si el usuario escogió calcularlas en la TIERRA, salimos
    if (!mediasEnSatelite) return;

    // ---- Añadimos valores a la cola circular ----
    tempCola[idx] = t;
    humCola[idx] = h;

    idx = (idx + 1) % N;

    if (cont < N) cont++;

    nuevos++; // cuántos nuevos llevamos desde la última media enviada

    // -------- Cuando hemos metido 10 valores NUEVOS --------
    if (cont == N && nuevos == N) {

        // Sumamos y calculamos medias
        float sumaT = 0, sumaH = 0;

        for (int i = 0; i < cont; i++) {
            sumaT += tempCola[i];
            sumaH += humCola[i];
        }

        mediaT = sumaT / cont;
        mediaH = sumaH / cont;

        // Construimos mensaje: 5:Tmedia:Hmedia
        char mensaje[50];
        sprintf(mensaje, "5:%.2f:%.2f", mediaT, mediaH);

        int checksum = hacerChecksum(mensaje);

        enlace.print(mensaje);
        enlace.print("|");
        enlace.println(checksum);

        delay(50);

        // Reseteamos el contador
        nuevos = 0;

        // -------- SISTEMA DE ALERTAS --------
        // Si temperatura media supera límite 3 veces seguidas → alarma
        if (mediaT >= valorlimiteT) {
            jT++;
            if (jT >= 3)
                enlace.println("6:|112");  // Código de error medias
        } else jT = 0;

        // Igual para humedad
        if (mediaH >= valorlimiteH) {
            jH++;
            if (jH >= 3)
                enlace.println("6:|112");
        } else jH = 0;
    }
}
//////////////////////////////////////////////////////////////
// =================== SIMULACIÓN ORBITAL ==================
//////////////////////////////////////////////////////////////
//
//
//////////////////////////////////////////////////////////////

void simularPosicion(unsigned long tiempo_ms, double inclination, int ecef) {

    // Convertimos tiempo Arduino → tiempo "orbital"
    double time = (tiempo_ms / 1000.0) * TIME_COMPRESSION;

    // Ángulo orbital correspondiente (0 → 360°)
    double angle = 2 * PI * (time / real_orbital_period);

    // Coordenadas básicas en la órbita (suponemos un círculo)
    double x = r * cos(angle);
    double y = r * sin(angle) * cos(inclination);
    double z = r * sin(angle) * sin(inclination);

    // Si queremos coordenadas ECEF → la Tierra gira
    if (ecef) {
        double theta = EARTH_ROTATION_RATE * time;

        double x_ecef = x * cos(theta) - y * sin(theta);
        double y_ecef = x * sin(theta) + y * cos(theta);

        x = x_ecef;
        y = y_ecef;
    }

    // Enviamos al PC
    enviarPosicion(x, y, z);
}


void enviarPosicion(double x, double y, double z) {
    // Formato del mensaje:
    //      9:x:y:z
    char mensaje[80];
    sprintf(mensaje, "9:%.2f:%.2f:%.2f", x, y, z);

    int checksum = hacerChecksum(mensaje);

    enlace.print(mensaje);
    enlace.print("|");
    enlace.println(checksum);
}



//////////////////////////////////////////////////////////////
// ======================== TIMEOUT =========================
//////////////////////////////////////////////////////////////
//
// Si algún sensor deja de mandar datos durante demasiado tiempo,
// enviamos códigos de error a la estación tierra.
//
//////////////////////////////////////////////////////////////

void verificarTimeout() {

  // ----------- TEMP/HUM -----------
  if (transmitirTH && (millis() - ultimoDatoOKTempHum > timeoutFallo)) {

    // Código 2 = error temp/hum
    enlace.println("2:|108");   // checksum ya calculado previamente

    // Reiniciamos el timer para evitar spam
    ultimoDatoOKTempHum = millis();
  }


  // ----------- DISTANCIA -----------
  if (transmitirDist && (millis() - ultimoDatoOKdist > timeoutFallo)) {

    // Código 4 = error distancia
    enlace.println("4:|110");

    ultimoDatoOKdist = millis();
  }


  // ----------- POSICIÓN -----------
  if (transmitirPos && (millis() - ultimoDatoOKPos > timeoutFallo)) {

    // Código 10 = error órbita
    enlace.println("10:|155");

    ultimoDatoOKPos = millis();
  }
}



//////////////////////////////////////////////////////////////
// ======================== LOOP ============================
//////////////////////////////////////////////////////////////
// TODO el trabajo
// está repartido en funciones separadas.
// Aquí simplemente:
//     1. Leemos si llegan comandos desde Python
//     2. Llamamos a cada sensor según su periodo
//     3. Actualizamos posición orbital
//     4. Verificamos timeouts
//
//////////////////////////////////////////////////////////////

void loop() {

  ////////////////////////////////////////////////////////////
  // 1. Leemos comandos que llegan de python
  ////////////////////////////////////////////////////////////
  if (enlace.available() > 0) {
    String cmd = enlace.readStringUntil('\n');
    procesarComando(cmd);
  }

  ///////////////////////////////////////////////////////////
  // 2. LECTURAS DE TEMPERATURA / HUMEDAD
  ////////////////////////////////////////////////////////////
  if (transmitirTH && millis() - lastReadTH >= periodoTempHum) {
    lastReadTH = millis();
    leerTemperaturaHumedad();
  }

  ////////////////////////////////////////////////////////////
  // 3. LECTURA DE DISTANCIA (RADAR)
  ////////////////////////////////////////////////////////////
  if (transmitirDist && millis() - lastReadDist >= periodoDist) {
    lastReadDist = millis();
    leerDistancia();
  }

  ////////////////////////////////////////////////////////////
  // 4. POSICIÓN ORBITAL
  ////////////////////////////////////////////////////////////
  if (transmitirPos && millis() - lastReadPos >= periodoPos) {
    lastReadPos = millis();

    // inclinación = 0 (puedes cambiarlo)
    // ecef = 0 → coordenadas simples, no rotación terrestre
    simularPosicion(millis(), 0, 0);
  }

  ////////////////////////////////////////////////////////////
  // 5. TIMEOUTS
  ////////////////////////////////////////////////////////////
  verificarTimeout();
}

