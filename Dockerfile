FROM python:3.11-slim

# 作業ディレクトリ設定
WORKDIR /app

# 依存関係インストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# データ・アップロード用ディレクトリを作成
RUN mkdir -p /app/data /app/uploads

# ポート公開
EXPOSE 8000

# 起動コマンド
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
