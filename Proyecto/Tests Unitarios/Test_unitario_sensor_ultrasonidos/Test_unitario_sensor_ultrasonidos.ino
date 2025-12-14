#define TRIG 4
#define ECHO 5

void setup() {
  Serial.begin(9600);
  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);
  Serial.println("Iniciando test de ultrasonido...");
}

void loop() {
  testUltrasonido();  // Aquí llamamos a la función de test
  delay(2000);        // Esperar 2 segundos entre mediciones
}

float medirDistanciaTest() {
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);
  long duracion = pulseIn(ECHO, HIGH, 30000);  // timeout 30ms
  if (duracion == 0) return NAN;
  float distancia = duracion * 0.0343 / 2;
  return distancia;
}

void testUltrasonido() {
  float d = medirDistanciaTest();
  if (isnan(d)) {
    Serial.println("No se detecta eco (fuera de rango o fallo)");
  } else if (d < 0 || d > 400) {
    Serial.println("Distancia fuera de rango");
  } else {
    Serial.print("Distancia medida correctamente: ");
    Serial.println(d);
  }
}








