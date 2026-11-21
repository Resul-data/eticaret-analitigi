import json
import random
import time
from datetime import datetime
from kafka import KafkaProducer

# Kafka (Redpanda) Bağlantısı
producer = KafkaProducer(
    bootstrap_servers=['localhost:19092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

TOPIC_NAME = 'user-clicks'
categories = ['Elektronik', 'Moda', 'Ev-Yasam', 'Kozmetik', 'Spor']
actions = ['view', 'add_to_cart', 'click']

print("Canlı veri akışı başlatıldı... Durdurmak için Ctrl+C")

try:
    while True:
        # Sahte e-ticaret log verisi üretimi
        log_data = {
            'user_id': random.randint(10000, 99999),
            'action': random.choice(actions),
            'category': random.choice(categories),
            'product_id': random.randint(500, 5000),
            'price': round(random.uniform(50.0, 5000.0), 2),
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Veriyi kuyruğa gönder
        producer.send(TOPIC_NAME, log_data)
        print(f"Gönderilen Log: {log_data}")

        # Gerçek zamanlı akış simülasyonu için rastgele bekleme (0.2 - 1 saniye)
        time.sleep(random.uniform(0.2, 1.0))

except KeyboardInterrupt:
    print("Akış durduruldu.")
finally:
    producer.close()
