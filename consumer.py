import os
import json
from datetime import datetime
from kafka import KafkaConsumer
from clickhouse_driver import Client
from dotenv import load_dotenv

load_dotenv()

# 1. ClickHouse Bağlantısı ve Tablo Oluşturma (Şifreli Yeni Sürüm)
ch_client = Client(host='localhost', port=9000, user='default', password=os.environ["CLICKHOUSE_PASSWORD"])

ch_client.execute('''
CREATE TABLE IF NOT EXISTS default.ecommerce_logs (
    user_id UInt32,
    action String,
    category String,
    product_id UInt32,
    price Float32,
    timestamp DateTime
) ENGINE = MergeTree()
ORDER BY (timestamp, user_id)
''')
print("ClickHouse tablosu hazır.")

# 2. Kafka Tüketici Bağlantısı
consumer = KafkaConsumer(
    'user-clicks',
    bootstrap_servers=['localhost:19092'],
    auto_offset_reset='latest',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

print("Kuyruk dinleniyor, veriler ClickHouse'a yazılıyor...")

# Canlı veriyi yakalayıp ClickHouse'a ekleme döngüsü
for message in consumer:
    log = message.value

    # KRİTİK DÜZELTME: Gelen String halindeki tarihi Python DateTime nesnesine çeviriyoruz
    log_time = datetime.strptime(log['timestamp'], '%Y-%m-%d %H:%M:%S')

    # ClickHouse'a ekleme sorgusu
    ch_client.execute(
        'INSERT INTO default.ecommerce_logs (user_id, action, category, product_id, price, timestamp) VALUES',
        [(log['user_id'], log['action'], log['category'], log['product_id'], log['price'], log_time)]
    )
    print(f"Veri tabanına yazıldı: User {log['user_id']} -> {log['action']}")
