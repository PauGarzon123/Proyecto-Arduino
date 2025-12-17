  #include <DHT.h>
  #include <Servo.h>
  #include <Wire.h>
  #include <SPI.h>
  #include <ArduCAM.h>
  #include "memorysaver.h"


  // ------------ DEFINICIÓN DE PINES ------------
  #define DHTPIN 6
  #define DHTTYPE DHT11
  #define TRIG 4
  #define ECHO 5
  #define SERVO 3
  #define CS_PIN 7
  #define PACKET_SIZE 32  // Tamaño de cada fragmento de imagen
  #define INTERVALO_IMAGEN 4000 // Retardo seguro entre paquetes de imagen

  ArduCAM myCAM(OV2640, CS_PIN);
  bool modoImagen = false;   // Flag para activar envío de imagen

  DHT dht(DHTPIN, DHTTYPE);
  Servo servoMotor;

  const int led1 = 13;

  // ------------ ESTADOS ------------
  bool transmitirTH = true;
  bool transmitirDist = true;
  bool transmitirPos = true;
  bool mediasEnSatelite = true;

  // ------------ TIMERS ------------
  unsigned long lastReadTH = 0;
  unsigned long lastReadDist = 0;
  unsigned long lastReadPos = 0;

  unsigned long ultimoDatoOKTempHum = 0;
  unsigned long ultimoDatoOKdist = 0;
  unsigned long ultimoDatoOKPos = 0;

  unsigned long periodoTempHum = 10200;
  unsigned long periodoDist =13000;
  unsigned long periodoPos = 15000;

  const unsigned long timeoutFallo = 150000;

  // ------------ SERVO RADAR ------------
  int angulo = 0;
  int incremento = 5;
  bool modoRastreo = true;
  int anguloFijo = 90;

  // ------------ MEDIAS ------------
  const int N = 10; // Tamaño del buffer circular
  float tempCola[N];
  float humCola[N];


  int idx = 0;       // Índice actual del buffer
  int cont = 0;      // Cantidad de datos acumulados
  int nuevos = 0;    // Contador de datos nuevos

  int jT = 0, jH = 0; // Contadores para alertas por límite

  float mediaT = 0;
  float mediaH = 0;

  float valorlimiteT = 100;
  float valorlimiteH = 100;

  // ------------ CONSTANTES ORBITA ------------
  const double G = 6.67430e-11;
  const double M = 5.97219e24;
  const double R_EARTH = 6371000;
  const double ALTITUDE = 400000;

  const double EARTH_ROTATION_RATE = 7.2921159e-5;
  const double TIME_COMPRESSION = 90.0;

  double real_orbital_period;
  double r;

  // ========================================================
  // ====================== SETUP ===========================
  // ========================================================
  void setup() {
    Wire.begin();
    SPI.begin();
    pinMode(CS_PIN, OUTPUT);
    digitalWrite(CS_PIN, HIGH);
    // Inicializa cámara ArduCAM con resolución 160x120 JPEG
    myCAM.set_format(JPEG);
    myCAM.InitCAM();
    myCAM.OV2640_set_JPEG_size(OV2640_160x120);
    myCAM.clear_fifo_flag();

    pinMode(led1, OUTPUT);
    pinMode(TRIG, OUTPUT);
    pinMode(ECHO, INPUT);

  
    Serial.begin(9600);

    dht.begin();
    servoMotor.attach(SERVO);

    r = R_EARTH + ALTITUDE;
    real_orbital_period = 2 * PI * sqrt(pow(r, 3) / (G * M));

  }

  // ========================================================
  // ===================== CHECKSUM =========================
  // ========================================================
  // Calcula checksum modulo 256 de una cadena
  // Entrada: cadenaf[] = cadena de caracteres
  // Salida: valor checksum (0-255)

  int hacerChecksum(const char cadenaf[]) {
    int suma = 0;
    for (int i = 0; i < strlen(cadenaf); i++)
      suma += cadenaf[i];
    return (suma % 256);
  }

  // ========================================================
  // ============= ENVÍO DE TEMPERATURA =====================
  // ========================================================
  // Envía por Serial temperatura y humedad con formato y checksum
  // Entrada: t = temperatura (°C), h = humedad (%)


  void enviarTemperatura(float t, float h) {
    digitalWrite(led1, HIGH);

    String s = "1:";
    s += String(t, 2);
    s += ":";
    s += String(h, 2);

    int checksum = hacerChecksum(s.c_str());

    Serial.print(s);
    Serial.print("|");
    Serial.println(checksum);

    digitalWrite(led1, LOW);
  }

  // ========================================================
  // ============= ENVÍO DE DISTANCIA ========================
  // ========================================================
  // Envía por Serial la distancia medida y ángulo del radar
  // Entrada: d = distancia (cm), ang = ángulo servo (°)


  void enviarDistancia(float d, int ang) {
    digitalWrite(led1, HIGH);

    String s = "3:";
    s += String(d, 2);
    s += ":";
    s += String(ang);

    int checksum = hacerChecksum(s.c_str());

    Serial.print(s);
    Serial.print("|");
    Serial.println(checksum);

    digitalWrite(led1, LOW);
  }

  // ========================================================
  // =================CALCULAR Y ENVIAR MEDIAS =====================
  // ========================================================
  // Calcula medias de N últimas lecturas de temperatura y humedad
  // Envía resultado y controla alertas si supera límites
  // Entrada: t = temperatura actual, h = humedad actual

  void calcularEnviarMedias(float t, float h) {
    if (!mediasEnSatelite) return;

    tempCola[idx] = t;
    humCola[idx] = h;

    idx = (idx + 1) % N;
    if (cont < N) cont++;
    nuevos++;

    if (cont == N && nuevos == N) {
      float sumaT = 0, sumaH = 0;

      for (int i = 0; i < N; i++) {
        sumaT += tempCola[i];
        sumaH += humCola[i];
      }

      mediaT = sumaT / N;
      mediaH = sumaH / N;

      String s = "5:";
      s += String(mediaT, 2);
      s += ":";
      s += String(mediaH, 2);

      int checksum = hacerChecksum(s.c_str());

      Serial.print(s);
      Serial.print("|");
      Serial.println(checksum);

      nuevos = 0;
      // Control de alertas si media supera límites
      if (mediaT >= valorlimiteT) {
        jT++;
        if (jT >= 3) Serial.println("6:|112");
      } else jT = 0;

      if (mediaH >= valorlimiteH) {
        jH++;
        if (jH >= 3) Serial.println("6:|112");
      } else jH = 0;
    }
  }

// ==================== ENVÍO POSICIÓN ORBITAL ====================
// Envía coordenadas simuladas del satélite por Serial
// Entrada: x, y, z = posición en km

  void enviarPosicion(double x, double y, double z) {
    String s = "9:";
    s += String(x, 2);
    s += ":";
    s += String(y, 2);
    s += ":";
    s += String(z, 2);

    int checksum = hacerChecksum(s.c_str());

    Serial.print(s);
    Serial.print("|");
    Serial.println(checksum);
  }
// ==================== SIMULACIÓN POSICIÓN ====================
// Calcula posición orbital simulada y envía
// Entrada: tiempo_ms = tiempo en ms desde inicio
//          inclination = inclinación orbital (rad)
//          ecef = 1 para convertir a coordenadas ECEF, 0 sin conversión
// Salida: ningún valor de retorno
  void simularPosicion(unsigned long tiempo_ms, double inclination, int ecef) {
    double time = (tiempo_ms / 1000.0) * TIME_COMPRESSION;
    double angle = 2 * PI * (time / real_orbital_period);

    double x_m = r * cos(angle);
    double y_m = r * sin(angle) * cos(inclination);
    double z_m = r * sin(angle) * sin(inclination);

    if (ecef) {
      double theta = EARTH_ROTATION_RATE * time;
      double x_ecef = x_m * cos(theta) - y_m * sin(theta);
      double y_ecef = x_m * sin(theta) + y_m * cos(theta);

      x_m = x_ecef;
      y_m = y_ecef;
    }

    enviarPosicion(x_m / 1000.0, y_m / 1000.0, z_m / 1000.0);
  }

  // ========================================================
  // ===================== LECTURAS ==========================
  // Lectura de sensores y control de alarmas
  // ========================================================
  void leerTemperaturaHumedad() {
    float h = dht.readHumidity();
    float t = dht.readTemperature();
     // Alarmas por superar límites de temp y hum
    if (t > valorlimiteT) {
      Serial.println("ALARM:temperatura excesiva");
  } 
    if (h > valorlimiteH) {
      Serial.println("ALARM:humedad excesiva");
  }

    if (isnan(h) || isnan(t)) return;

    ultimoDatoOKTempHum = millis();

    enviarTemperatura(t, h);
    calcularEnviarMedias(t, h);
  }
  // ==================== MEDIR DISTANCIA ULTRASÓNICA ====================
  // Retorna: distancia medida en cm o NAN si no hay eco
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

  void leerDistancia() {
    int ang;

    if (modoRastreo) ang = moverServo();
    else {
      servoMotor.write(anguloFijo);
      ang = anguloFijo;
    }

    float d = medirDistancia();
    if (isnan(d)) return;

    ultimoDatoOKdist = millis();
    enviarDistancia(d, ang);
  }

  // ========================================================
  // ===================== TIMEOUTS ==========================
  // Control de fallos por falta de datos válidos
  // ========================================================
  void verificarTimeout() {
    if (transmitirTH && millis() - ultimoDatoOKTempHum > timeoutFallo) {
      Serial.println("2:|108");
      ultimoDatoOKTempHum = millis();
    }

    if (transmitirDist && millis() - ultimoDatoOKdist > timeoutFallo) {
      Serial.println("4:|110");
      ultimoDatoOKdist = millis();
    }

    if (transmitirPos && millis() - ultimoDatoOKPos > timeoutFallo) {
      Serial.println("10:|155");
      ultimoDatoOKPos = millis();
    }
  }

  // ========================================================
  // ====================== COMANDOS =========================
  // Interpreta comandos recibidos por Serial y los ejecuta
  // Entrada: cmd = comando recibido por Serial. Se pueden consultar en la tabla del protocolo en el readme
  void procesarComando(String cmd) {
    cmd.trim();
    int sep = cmd.indexOf('|');
    String mensaje = cmd.substring(0, sep);
    int checksumRecibido = cmd.substring(sep + 1).toInt();

    int checksumCalc = hacerChecksum(mensaje.c_str());
  if (checksumCalc != checksumRecibido) {
      Serial.println("ALARM:mensaje corrupto");
      return;
  }

    int fin = mensaje.indexOf(':');
    int codigo = mensaje.substring(0, fin).toInt();
    String params = mensaje.substring(fin + 1);

    if (codigo == 1) { //parar envio datos temp/hum
      transmitirTH = false;
    }
    else if (codigo == 2) {//reanudar envio datos temp/hum   
      transmitirTH = true;
    }
    else if (codigo == 3) {//parar envio datos dist
      transmitirDist = false;
    }
    else if (codigo == 4) {//reanudar envio datos dist
      transmitirDist = true;
    }
    else if (codigo == 5) {//nuevo periodo de datos temp/hum
      periodoTempHum = params.toInt();
    }
    else if (codigo == 6) {//nuevo periodo de datos dist
      periodoDist = params.toInt();
    }
    else if (codigo == 7) {//sensor de distancia modo rastreo
      modoRastreo = true;
    }
    else if (codigo == 8) {//angulo nuevo y activar modo manual
      anguloFijo = params.toInt();
      if (anguloFijo < 0) anguloFijo = 0;
      if (anguloFijo > 180) anguloFijo = 180;
      modoRastreo = false;
    }
    else if (codigo == 10) {//hacer las medias en el satélite
      mediasEnSatelite = true;
    }
    else if (codigo == 11) {//hacer las medias en la estación tierra
      mediasEnSatelite = false;
    }
    else if (codigo == 12) {//valor limite de la media temp/hum
      int pos = params.indexOf(':');
      valorlimiteT = params.substring(0, pos).toFloat();
      valorlimiteH = params.substring(pos + 1).toFloat();
    }
  }
// ========================================================
// ================= CRC-8 BINARIO ========================
// Verificación de integridad de paquetes de imagen
// ========================================================
uint8_t crc8(uint8_t *data, int len) {
  uint8_t crc = 0;
  for (int i = 0; i < len; i++) crc ^= data[i];
  return crc;
}

// ========================================================
// ================= BYTE → HEX ===========================
// Convierte un byte a cadena hexadecimal
// ========================================================
String toHex(byte b) {
  const char hexmap[] = "0123456789ABCDEF";
  String s = "";
  s += hexmap[b >> 4];
  s += hexmap[b & 0x0F];
  return s;
}

// ========================================================
// ================= ESPERA ACK ===========================
// Espera confirmación de recepción de paquete de imagen
// ========================================================
bool waitForACK(uint16_t id) {
  unsigned long start = millis();
  String esperado = "ACK " + String(id);

  while (millis() - start < 5000) {
    if (Serial.available()) {
      String rx = Serial.readStringUntil('\n');
      rx.trim();
      if (rx == esperado) return true;
    }
  }
  return false;
}
// ========================================================
// ================= ENVÍO DE IMAGEN =====================
// Captura imagen, la divide en paquetes, calcula CRC, envía y espera ACK
// ========================================================
void enviarImagen() {

  myCAM.flush_fifo(); // Vacía cualquier dato previo en la memoria FIFO
  myCAM.clear_fifo_flag();
  myCAM.start_capture();
  while (!myCAM.get_bit(ARDUCHIP_TRIG, CAP_DONE_MASK));// Espera hasta que la captura termine
  // Obtiene la longitud total de la imagen en bytes
  uint32_t length = myCAM.read_fifo_length();
  if (length == 0) return;

  uint16_t pid = 0;  // ID del paquete (incremental)
  uint32_t index = 0; // Índice de lectura de bytes

  myCAM.CS_LOW();
  // Mientras no hayamos leído toda la imagen
  while (index < length) {

    uint8_t raw[PACKET_SIZE]; // Buffer temporal para almacenar el paquete
    int raw_len = 0;
     // Llenar el paquete con PACKET_SIZE bytes o hasta el final de la imagen
    while (raw_len < PACKET_SIZE && index < length) {
      raw[raw_len++] = myCAM.read_fifo();// Leer un byte de la FIFO
      index++;
    }
    // Calcular CRC-8 del paquete para verificación de errores
    uint8_t crc = crc8(raw, raw_len);
    // Construir el mensaje de transmisión en formato:
    // 99:<ID_paquete>:<datos en HEX>:<CRC>
    String msg = "99:" + String(pid) + ":";
    for (int i = 0; i < raw_len; i++) msg += toHex(raw[i]);
    msg += ":" + String(crc);

    Serial.println(msg);
    // Esperar ACK del receptor. Si no llega, volver a enviar el paquete
    if (!waitForACK(pid)) continue;

    delay(INTERVALO_IMAGEN);  // Retardo para evitar saturar LoRa
    pid++;
  }

  myCAM.CS_HIGH();
}



  // ========================================================
  // ======================== LOOP ===========================
  // Control principal: lectura sensores, transmisión y comandos
  // ========================================================
void loop() {

  // ======== ESCUCHA Y MUESTRA LO QUE LLEGA =========
  if (Serial.available() > 0) {

    // Leer comando crudo
    String comandoRecibido = Serial.readStringUntil('\n');
    comandoRecibido.trim();

    // COMANDO ESPECIAL IMAGEN
    if (comandoRecibido == "99:") {
      modoImagen = true;
    } 
    else {
      // Procesarlo como siempre
      procesarComando(comandoRecibido);
    }
  }

  // ======== MODO IMAGEN (EXCLUSIVO) =========
  if (modoImagen) {
    enviarImagen();    ¡
    modoImagen = false;  // volver a modo normal
    return;              
  }

  // ======== RESTO DEL CÓDIGO SIN CAMBIOS =========

  if (transmitirTH && millis() - lastReadTH >= periodoTempHum) {
    lastReadTH = millis();
    leerTemperaturaHumedad();
  }

  if (transmitirDist && millis() - lastReadDist >= periodoDist) {
    lastReadDist = millis();
    leerDistancia();
  }

  if (transmitirPos && millis() - lastReadPos >= periodoPos) {
    lastReadPos = millis();
    double inclinacion = 51.6 * PI / 180.0;
    simularPosicion(millis(), inclinacion, 0);
  }

  verificarTimeout();
}


