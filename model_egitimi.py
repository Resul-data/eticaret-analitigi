import os
import mlflow
import mlflow.sklearn
import pandas as pd
import clickhouse_connect
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from dotenv import load_dotenv

load_dotenv()

# 1. ClickHouse'dan Eğitimsiz Canlı Verileri Çekme
print("🔄 ClickHouse'dan model eğitimi için canlı veriler çekiliyor...")
client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password=os.environ["CLICKHOUSE_PASSWORD"])

query_result = client.query('SELECT action, category, price FROM default.ecommerce_logs')
df = pd.DataFrame(query_result.result_rows, columns=['action', 'category', 'price'])

if len(df) < 50:
    print(f"⚠ İçeride yeterli veri yok (Şu anki veri sayısı: {len(df)}). Lütfen veri tabanında en az 50 satır birikene kadar bekleyin!")
    exit()

# 2. Veri Ön İşleme (Feature Engineering)
# Kategorik verileri sayısal verilere dönüştürüyoruz (One-Hot Encoding)
df = pd.get_dummies(df, columns=['action', 'category'], drop_first=True)

# HEDEF DEĞİŞKEN (Target): Eğer harcanan para 2500 TL'den büyükse 1 (Premium Sepet), küçükse 0
df['is_premium_basket'] = (df['price'] > 2500).astype(int)

# Modeli eğitirken fiyatın kendisini kopya çekmesin diye siliyoruz
X = df.drop(columns=['price', 'is_premium_basket'])
y = df['is_premium_basket']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)


# 3. MLflow Deney Takibi Başlatma
print("🚀 MLflow Deneyi başlatılıyor...")
mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_experiment("E-Ticaret_Kullanici_Skorlama")

with mlflow.start_run():
    # Hiperparametreler
    n_estimators = 100
    max_depth = 5

    # Model Kurulumu (Random Forest)
    model = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, random_state=42)
    model.fit(X_train, y_train)

    # Tahmin ve Metrik Hesaplama
    predictions = model.predict(X_test)
    acc = accuracy_score(y_test, predictions)

    print(f"✅ Model Eğitildi! Doğruluk Skoru (Accuracy): {acc:.2f}")

    # PARAMETRELERİ MLFLOW'A KAYDET
    mlflow.log_param("n_estimators", n_estimators)
    mlflow.log_param("max_depth", max_depth)

    # METRİKLERİ MLFLOW'A KAYDET
    mlflow.log_metric("accuracy", acc)

    # MODELİN KENDİSİNİ MLFLOW'A KAYDET
       # Modelin kendisini MLflow'a kaydet (Doğru Fonksiyon)
       # MLflow'a Random Forest model bileşenlerine güvendiğimizi açıkça belirterek kaydediyoruz
    mlflow.sklearn.log_model(
        model,
        name="rf_model",
        skops_trusted_types=["sklearn.tree._tree.Tree"]
    )
    print("📦 Model ve tüm metrikler başarıyla MLflow sistemine mühürlendi!")
