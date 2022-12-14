from paho.mqtt.client import Client

mqttBroker ="mqtt.eclipseprojects.io"

if __name__ == '__main__':
    client = Client("Publisher_test")

    def on_publish(client, userdata, mid):
        print("Messaggio pubblicato")

    client.on_publish = on_publish

    client.connect(mqttBroker)
    client.loop_start()

    messaggio = input("Inserisci il testo da inviare al topic test")
    client.publish(topic = "test", payload = messaggio)

    client.loop_stop()
    client.disconnect()