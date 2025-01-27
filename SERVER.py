from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import asyncio
from paho.mqtt.client import Client as MQTTClient
import datetime
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with a strong secret key

# MQTT Configuration
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPICS = {
    "row1": "esp8266/ledmatrix",
    "row2": "esp8266/ledmatrix1",
    "row3": "esp8266/ledmatrix2"
}

# Initialize the MQTT client
mqtt_client = MQTTClient()

# Directory for saving messages
MESSAGE_DIR = "messages"

# Ensure the messages directory exists
if not os.path.exists(MESSAGE_DIR):
    os.makedirs(MESSAGE_DIR)

# Valid Key for sending message
valid_key = "srjec"  # Replace with the key you want


# Save message with timestamp to a file
def save_message_to_file(timestamp, topic, message):
    """
    Save the received message to a daily file.
    """
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = os.path.join(MESSAGE_DIR, f"{current_date}.txt")

    with open(filename, "a") as file:
        file.write(f"{timestamp} - {topic} - {message}\n")


# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT Broker: {MQTT_BROKER}")
    for topic in MQTT_TOPICS.values():
        client.subscribe(topic)
    print("Subscribed to all topics.")


def on_message(client, userdata, msg):
    message = msg.payload.decode()
    topic = msg.topic
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"Received: {message} from {topic} at {timestamp}")
    save_message_to_file(timestamp, topic, message)


mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message


# Connect to MQTT in a background thread
def start_mqtt():
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()


# Flask Routes
@app.route("/")
def index():
    return render_template("index.html", topics=list(MQTT_TOPICS.keys()))


@app.route("/send", methods=["POST"])
def send_message():
    """
    Endpoint to handle message submission from the frontend.
    """
    data = request.json
    message = data.get("message")
    row = data.get("row")
    key = data.get("key")  # Get the key from the request

    if key != valid_key:
        return jsonify({"status": "error", "message": "Invalid key."}), 400  # Key mismatch

    if row in MQTT_TOPICS and message:
        topic = MQTT_TOPICS[row]
        mqtt_client.publish(topic, message)
        print(f"Message sent to {topic}: {message}")
        return jsonify({"status": "success", "message": "Message sent successfully."})

    return jsonify({"status": "error", "message": "Invalid row or message missing."}), 400


# Main Execution
if __name__ == "__main__":
    start_mqtt()
    app.run(host="0.0.0.0", port=5000)
