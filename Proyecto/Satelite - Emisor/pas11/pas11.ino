  #include <DHT.h>
  #include <Servo.h>

  // ------------ DEFINICIÓN DE PINES ------------
  #define DHTPIN 6
  #define DHTTYPE DHT11
  #define TRIG 4
  #define ECHO 5
  #define SERVO 3

  DHT dht(DHTPIN, DHTTYPE);
  Servo servoMotor;
  //  ⬇️ ELIMINO SoftwareSerial
  //SoftwareSerial enlace(10, 11);

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

  unsigned long periodoTempHum = 500;
  unsigned long periodoDist = 800;
  unsigned long periodoPos = 500;

  const unsigned long timeoutFallo = 7000;

  // ------------ SERVO RADAR ------------
  int angulo = 0;
  int incremento = 5;
  bool modoRastreo = true;
  int anguloFijo = 90;

  // ------------ MEDIAS ------------
  const int N = 10;
  float tempCola[N];
  float humCola[N];

  int idx = 0;
  int cont = 0;
  int nuevos = 0;

  int jT = 0, jH = 0;

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
    pinMode(led1, OUTPUT);
    pinMode(TRIG, OUTPUT);
    pinMode(ECHO, INPUT);

  
    Serial.begin(115200);

    dht.begin();
    servoMotor.attach(SERVO);

    r = R_EARTH + ALTITUDE;
    real_orbital_period = 2 * PI * sqrt(pow(r, 3) / (G * M));

    Serial.println("Emisor listo. Esperando comandos START/STOP...");
  }

  // ========================================================
  // ===================== CHECKSUM =========================
  // ========================================================
  int hacerChecksum(const char cadenaf[]) {
    int suma = 0;
    for (int i = 0; i < strlen(cadenaf); i++)
      suma += cadenaf[i];
    return (suma % 256);
  }

  // ========================================================
  // ============= ENVÍO DE TEMPERATURA =====================
  // ========================================================
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
  // ===================== ENVIAR MEDIAS =====================
  // ========================================================
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

  // ========================================================
  // ===================== ENVIÓ ORBITAL =====================
  // ========================================================
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
  // ========================================================
  void leerTemperaturaHumedad() {
    float h = dht.readHumidity();
    float t = dht.readTemperature();

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
  // ========================================================
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

    if (codigo == 1) { 
      transmitirTH = false;
    }
    else if (codigo == 2) {
      transmitirTH = true;
    }
    else if (codigo == 3) {
      transmitirDist = false;
    }
    else if (codigo == 4) {
      transmitirDist = true;
    }
    else if (codigo == 5) {
      periodoTempHum = params.toInt();
    }
    else if (codigo == 6) {
      periodoDist = params.toInt();
    }
    else if (codigo == 7) {
      modoRastreo = true;
    }
    else if (codigo == 8) {
      anguloFijo = params.toInt();
      if (anguloFijo < 0) anguloFijo = 0;
      if (anguloFijo > 180) anguloFijo = 180;
      modoRastreo = false;
    }
    else if (codigo == 10) {
      mediasEnSatelite = true;
    }
    else if (codigo == 11) {
      mediasEnSatelite = false;
    }
    else if (codigo == 12) {
      int pos = params.indexOf(':');
      valorlimiteT = params.substring(0, pos).toFloat();
      valorlimiteH = params.substring(pos + 1).toFloat();
    }
  }


  // ========================================================
  // ======================== LOOP ===========================
  // ========================================================
  void loop() {

    if (Serial.available() > 0)
      procesarComando(Serial.readStringUntil('\n'));

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
      simularPosicion(millis(), 0, 0);
    }

    verificarTimeout();
  }
