#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <DHTesp.h>

const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASSWORD = "";

const char* MQTT_SERVER = "broker.hivemq.com";
const int MQTT_PORT = 1883;
const char* MQTT_TOPIC = "ptit/iot/esp32/telemetry_bminh";

#define DHT_PIN 15
#define TRIG_PIN 5
#define ECHO_PIN 18
#define LED_PIN 2

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);
DHTesp dht;

unsigned long lastSend = 0;
unsigned long sequence = 0;

void connectWiFi() {
  Serial.print("Connecting WiFi");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD, 6);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" OK");
}

void connectMQTT() {
  while (!mqtt.connected()) {
    Serial.print("Connecting MQTT...");

    // Tạo Client ID ngẫu nhiên để tránh đụng độ trên Public Broker
    String clientId = "ESP32_B23DCCN538_";
    clientId += String(random(0xffff), HEX);

    if (mqtt.connect(clientId.c_str())) {
      Serial.println(" OK");
    } else {
      Serial.print(" FAILED, rc=");
      Serial.print(mqtt.state());
      Serial.println(" retrying in 2 seconds...");
      delay(2000);
    }
  }
}

float readDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  unsigned long time = pulseIn(ECHO_PIN, HIGH, 30000);
  if (time == 0) return NAN;
  return time * 0.0343 / 2;
}

void setup() {
  Serial.begin(115200);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);

  dht.setup(DHT_PIN, DHTesp::DHT22);
  connectWiFi();
  mqtt.setServer(MQTT_SERVER, MQTT_PORT);
  Serial.println("ESP32 START");
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) connectWiFi();
  if (!mqtt.connected()) connectMQTT();
  mqtt.loop();

  if (millis() - lastSend < 5000) return;
  lastSend = millis();

  TempAndHumidity data = dht.getTempAndHumidity();
  float distance = readDistance();

  if (!isfinite(data.temperature) || !isfinite(data.humidity) || !isfinite(distance)) {
    Serial.println("Sensor error!");
    return;
  }

  sequence++;
  char payload[200];

  snprintf(payload, sizeof(payload),
    "{\"temperature\":%.2f,"
    "\"humidity\":%.2f,"
    "\"distance_cm\":%.2f,"
    "\"rssi\":%d,"
    "\"sequence\":%lu,"
    "\"uptime_s\":%lu}",
    data.temperature,
    data.humidity,
    distance,
    WiFi.RSSI(),
    sequence,
    millis() / 1000
  );

  // Publish trực tiếp vào topic riêng chứa mã sinh viên B23DCCN538
  bool ok = mqtt.publish(MQTT_TOPIC, payload);

  Serial.println(payload);
  Serial.println(ok ? "PUBLISH OK" : "PUBLISH FAILED");

  digitalWrite(LED_PIN, HIGH);
  delay(80);
  digitalWrite(LED_PIN, LOW);
}