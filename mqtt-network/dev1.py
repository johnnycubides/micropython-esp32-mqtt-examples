import time
import network
from umqtt.simple import MQTTClient
from machine import Pin, ADC, UART

# NETWORK
SSID = "luna"
PASSWORD = "password"
# MQTT DEFINITIONS
MQTT_BROKER = "192.168.2.105"
CLIENT_ID = "dev1"
TOPIC_LED = CLIENT_ID + "/led"
TOPIC_ADC = CLIENT_ID + "/adc"
TOPIC_UART = CLIENT_ID + "/uart"
# PERIPHERALS DEFINITIONS
LED_PIN = 2
BUTTON_PIN = 0
ADC_PIN = 32
TX_PIN = 17
RX_PIN = 16
BAUDRATE = 57600  # 9600 57600 115200

# Make objects for peripherals
led = Pin(LED_PIN, Pin.OUT)
adc = ADC(ADC_PIN)
user_button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
uart_fpga = UART(2, baudrate=BAUDRATE, tx=17, rx=16)


# Callback mqtt
def subscribe_callback(topic, msg):
    topic = topic.decode("utf-8")
    msg = msg.decode("utf-8")
    print((topic, msg))
    # Callback actions
    if topic == TOPIC_LED:
        if msg == "on":
            led.value(1)
        elif msg == "off":
            led.value(0)


def connect_mqtt():
    client = MQTTClient(CLIENT_ID, MQTT_BROKER)
    client.set_callback(subscribe_callback)
    client.connect()
    client.subscribe(TOPIC_LED)
    print(f"Conectado a {MQTT_BROKER}, suscrito a {TOPIC_LED}")
    return client


def connectSTA(ssid, pwd):
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print("connecting to network...")
        sta_if.active(True)
        sta_if.connect(ssid, pwd)
        while not sta_if.isconnected():
            pass
    print("network config:", sta_if.ifconfig())


# Función principal
def main():
    # 1. Conectarse a una RED WIFI
    connectSTA(SSID, PASSWORD)
    # 2. Conectarse al broker mqtt y subscribirse a los topics
    mqtt_client = connect_mqtt()
    print("Esperando datos UART o mensajes MQTT...")

    while True:
        try:
            # 3. Verificar si existen mensajes de entrada por mqtt
            mqtt_client.check_msg()
        except Exception as e:
            print(e)
            # En el caso de desconectarse del broker, reintentar conexión
            mqtt_client = connect_mqtt()
        print("waiting")
        # 4. Verificar si se ha pulsado el botón
        if user_button.value() == 0:
            adc_value = adc.read()
            print(adc_value)
            mqtt_client.publish(TOPIC_ADC, str(adc_value))
        # 5. Verificar si se ha recibido datos por UART
        if uart_fpga.any():
            mqtt_client.publish(TOPIC_UART, str(uart_fpga.read()))
        # 6. Esperar un tiempo antes de hacer el loop
        time.sleep(0.1)


if __name__ == "__main__":
    main()
