# Pythonイメージ側でも日本語ロケール設定
FROM python:3.9-slim-buster

WORKDIR /app

# 日本語ロケール設定
RUN apt-get update && \
    apt-get install -y locales && \
    sed -i -e 's/# ja_JP.UTF-8 UTF-8/ja_JP.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen ja_JP.UTF-8
ENV LANG ja_JP.UTF-8
ENV LC_ALL ja_JP.UTF-8

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY . .

EXPOSE 5000

# Flaskアプリケーションを起動するコマンドに変更
# FLASK_APP環境変数を設定し、flask run を実行
ENV FLASK_APP=app.py
CMD ["flask", "run", "--host=0.0.0.0"]