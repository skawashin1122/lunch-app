import os
import sys
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pymysql.cursors
from dotenv import load_dotenv

# 文字化け対策：標準出力のエンコーディングを設定
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# 文字化け対策を強化したDB設定
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'db': os.getenv('MYSQL_DATABASE'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
    'init_command': 'SET NAMES utf8mb4',
    'use_unicode': True,
    'sql_mode': "TRADITIONAL",
    'autocommit': True
}

def get_db_connection():
    try:
        connection = pymysql.connect(**DB_CONFIG)
        # 接続後に文字セットを再確認
        with connection.cursor() as cursor:
            cursor.execute("SET NAMES utf8mb4")
            cursor.execute("SET CHARACTER SET utf8mb4")
            cursor.execute("SET character_set_connection=utf8mb4")
        return connection
    except Exception as e:
        app.logger.error(f"DB接続エラー: {e}")
        return None

@app.route('/')
def index():
    conn = get_db_connection()
    if conn is None:
        return render_template('result.html', success=False, message='データベースに接続できませんでした。')

    try:
        with conn.cursor() as cursor:
            # 文字セット確認（デバッグ用）
            cursor.execute("SELECT @@character_set_connection, @@collation_connection")
            charset_info = cursor.fetchone()
            app.logger.info(f"DB文字セット: {charset_info}")
            
            cursor.execute("SELECT id, name, price, description, image_url FROM products ORDER BY id")
            products = cursor.fetchall()
            
            # デバッグ用：取得したデータの確認
            for product in products:
                app.logger.info(f"商品データ: {product['name']}")
    except Exception as e:
        app.logger.error(f"商品データ取得エラー: {e}")
        products = []
    finally:
        conn.close()

    if 'cart' not in session:
        session['cart'] = []

    return render_template('index.html', products=products, cart=session['cart'])

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_id = int(request.form['product_id'])
    quantity = int(request.form['quantity'])

    conn = get_db_connection()
    if conn is None:
        return jsonify({'success': False, 'message': 'データベースに接続できませんでした。'})

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, price, image_url FROM products WHERE id = %s", (product_id,))
            product = cursor.fetchone()
    except Exception as e:
        app.logger.error(f"商品取得エラー: {e}")
        product = None
    finally:
        conn.close()

    if product:
        found = False
        for item in session['cart']:
            if item['id'] == product_id:
                item['quantity'] += quantity
                found = True
                break
        if not found:
            session['cart'].append({
                'id': product['id'],
                'name': product['name'],
                'price': product['price'],
                'image_url': product.get('image_url', ''),
                'quantity': quantity
            })
        session.modified = True
        return jsonify({'success': True, 'message': 'カートに追加しました！', 'cart_items': len(session['cart'])})
    return jsonify({'success': False, 'message': '商品の追加に失敗しました。'})

@app.route('/update_cart', methods=['POST'])
def update_cart():
    product_id = int(request.form['product_id'])
    quantity = int(request.form['quantity'])

    for item in session['cart']:
        if item['id'] == product_id:
            if quantity > 0:
                item['quantity'] = quantity
            else:
                session['cart'].remove(item)
            break
    session.modified = True
    return jsonify({'success': True, 'message': 'カートを更新しました。', 'cart_items': len(session['cart'])})

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    product_id = int(request.form['product_id'])
    session['cart'] = [item for item in session['cart'] if item['id'] != product_id]
    session.modified = True
    return jsonify({'success': True, 'message': '商品をカートから削除しました。', 'cart_items': len(session['cart'])})

@app.route('/confirm')
def confirm():
    if not session.get('cart'):
        return redirect(url_for('index'))

    total_price = sum(item['price'] * item['quantity'] for item in session['cart'])
    return render_template('confirm.html', cart=session['cart'], total_price=total_price)

@app.route('/checkout', methods=['POST'])
def checkout():
    customer_name = request.form.get('customer_name', '匿名')
    if not session.get('cart'):
        return redirect(url_for('index'))

    total_price = sum(item['price'] * item['quantity'] for item in session['cart'])
    conn = get_db_connection()
    if conn is None:
        return render_template('result.html', success=False, message='データベースに接続できませんでした。')

    try:
        with conn.cursor() as cursor:
            # 文字化け対策：明示的に文字セットを設定
            cursor.execute("SET NAMES utf8mb4")
            
            sql_order = "INSERT INTO orders (total_price, customer_name, status) VALUES (%s, %s, %s)"
            cursor.execute(sql_order, (total_price, customer_name, 'pending'))
            order_id = cursor.lastrowid

            sql_order_item = "INSERT INTO order_items (order_id, product_id, quantity, price_at_order) VALUES (%s, %s, %s, %s)"
            for item in session['cart']:
                cursor.execute(sql_order_item, (order_id, item['id'], item['quantity'], item['price']))
        
        conn.commit()
        session['last_order_id'] = order_id
        session.pop('cart', None)
        return redirect(url_for('result'))
    except Exception as e:
        conn.rollback()
        app.logger.error(f"注文処理中にエラーが発生しました: {e}")
        return render_template('result.html', success=False, message='注文処理中にエラーが発生しました。もう一度お試しください。')
    finally:
        conn.close()

@app.route('/result')
def result():
    order_id = session.pop('last_order_id', None)
    if order_id:
        return render_template('result.html', success=True, order_id=order_id)
    else:
        return render_template('result.html', success=False, message='注文情報が見つかりません。')

@app.route('/get_cart_preview')
def get_cart_preview():
    return jsonify({'cart': session.get('cart', [])})

# デバッグ用：文字セット確認エンドポイント
@app.route('/debug/charset')
def debug_charset():
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'DB接続エラー'})
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("SHOW VARIABLES LIKE 'character%'")
            charset_vars = cursor.fetchall()
            cursor.execute("SHOW VARIABLES LIKE 'collation%'")
            collation_vars = cursor.fetchall()
            
            return jsonify({
                'charset_vars': charset_vars,
                'collation_vars': collation_vars
            })
    finally:
        conn.close()

# 正常性チェック
@app.route('/health')
def health():
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)