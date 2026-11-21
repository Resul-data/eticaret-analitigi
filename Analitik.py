import os
import time
import clickhouse_connect
from dotenv import load_dotenv

load_dotenv()

# ClickHouse HTTP bağlantısı
client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password=os.environ["CLICKHOUSE_PASSWORD"])


def canli_analiz_raporu():
    print("\n" + "="*50)
    print(f" Canlı E-Ticaret Analitik Raporu ({time.strftime('%H:%M:%S')})")
    print("="*50)

    # Metrik 1: Son 1 dakika içinde sitede kaç benzersiz kullanıcı geziniyor?
    aktif_kullanici_query = client.query('''
        SELECT count(DISTINCT user_id) as aktif_sayi
        FROM default.ecommerce_logs
        WHERE timestamp >= now() - INTERVAL 1 MINUTE
    ''')
    # Sonucu güvenli bir şekilde alıyoruz
    aktif_sayi = aktif_kullanici_query.result_rows[0][0] if aktif_kullanici_query.result_rows else 0
    print(f"👉 Son 1 Dakikadaki Aktif Kullanıcı Sayısı: {aktif_sayi}")

    # Metrik 2: Son 5 dakikada en çok etkileşim alan (en trend) ilk 3 kategori
    print("\n🔥 Son 5 Dakikanın En Popüler Kategorileri:")
    trend_kategoriler = client.query('''
        SELECT category, count() as tiklanma
        FROM default.ecommerce_logs
        WHERE timestamp >= now() - INTERVAL 5 MINUTE
        GROUP BY category
        ORDER BY count() DESC
        LIMIT 3
    ''')
    for sira, row in enumerate(trend_kategoriler.result_rows, 1):
        print(f"  {sira}. {row[0]} ({row[1]} aksiyon)")

    # Metrik 3: Son 5 dakikada sepete en çok ürün ekleyen ilk 3 kullanıcı
    print("\n🛒 Son 5 Dakikada Sepetini En Çok Dolduran Kullanıcılar:")
    top_alicilar = client.query('''
        SELECT user_id, count() as sepet_sayisi, sum(price) as toplam_sepet_tutari
        FROM default.ecommerce_logs
        WHERE action = 'add_to_cart' AND timestamp >= now() - INTERVAL 5 MINUTE
        GROUP BY user_id
        ORDER BY sepet_sayisi DESC
        LIMIT 3
    ''')
    for row in top_alicilar.result_rows:
        print(f"  👤 User ID: {row[0]} -> {row[1]} Ürün ekledi | Toplam Değer: {row[2]:.2f} TL")

try:
    print("Analitik raporlama motoru başlatıldı... Çıkış için Ctrl+C")
    while True:
        canli_analiz_raporu()
        # Her 5 saniyede bir verileri yeniden sorgula
        time.sleep(5)
except KeyboardInterrupt:
    print("\nAnaliz durduruldu.")
