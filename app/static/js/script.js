document.addEventListener('DOMContentLoaded', () => {
    // カートに追加ボタンの処理 (index.html)
    document.querySelectorAll('.add-button').forEach(button => {
        button.addEventListener('click', (event) => {
            const productId = event.target.dataset.id;
            const quantityInput = document.querySelector(`.quantity-input[data-id="${productId}"]`);
            const quantity = parseInt(quantityInput.value);

            fetch('/add_to_cart', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `product_id=${productId}&quantity=${quantity}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(data.message);
                    updateCartCount(data.cart_items);
                    updateCartPreview(); // カートプレビューを更新
                    quantityInput.value = 1; // 数量をリセット
                } else {
                    alert(data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('カートへの追加に失敗しました。');
            });
        });
    });

    // 数量ボタンの処理 (index.html)
    document.querySelectorAll('.quantity-minus').forEach(button => {
        button.addEventListener('click', (event) => {
            const productId = event.target.dataset.id;
            const quantityInput = document.querySelector(`.quantity-input[data-id="${productId}"]`);
            let currentQuantity = parseInt(quantityInput.value);
            if (currentQuantity > 1) {
                quantityInput.value = currentQuantity - 1;
            }
        });
    });

    document.querySelectorAll('.quantity-plus').forEach(button => {
        button.addEventListener('click', (event) => {
            const productId = event.target.dataset.id;
            const quantityInput = document.querySelector(`.quantity-input[data-id="${productId}"]`);
            let currentQuantity = parseInt(quantityInput.value);
            quantityInput.value = currentQuantity + 1;
        });
    });

    // カート数量の表示を更新する関数
    function updateCartCount(count) {
        const cartCountElement = document.getElementById('cart-count');
        if (cartCountElement) {
            cartCountElement.textContent = count;
        }
    }

    // カートプレビューを更新する関数 (Ajaxでサーバーから最新のカート情報を取得)
    function updateCartPreview() {
        fetch('/get_cart_preview') // 新しく追加するエンドポイント
            .then(response => response.json())
            .then(data => {
                const currentCartItems = document.getElementById('current-cart-items');
                if (currentCartItems) {
                    currentCartItems.innerHTML = ''; // 一度クリア
                    if (data.cart && data.cart.length > 0) {
                        data.cart.forEach(item => {
                            const itemDiv = document.createElement('div');
                            itemDiv.classList.add('cart-item-preview');
                            itemDiv.innerHTML = `
                                <span>${item.name} x ${item.quantity}</span>
                                <span>¥${(item.price * item.quantity).toLocaleString()}</span>
                            `;
                            currentCartItems.appendChild(itemDiv);
                        });
                        // 注文確認ボタンを表示
                        const cartActions = document.querySelector('.cart-actions');
                        if (!cartActions) {
                            const newCartActions = document.createElement('div');
                            newCartActions.classList.add('cart-actions');
                            newCartActions.innerHTML = `<a href="/confirm" class="button primary-button">注文内容を確認する</a>`;
                            currentCartItems.parentNode.appendChild(newCartActions);
                        }
                    } else {
                        currentCartItems.innerHTML = '<p>カートはまだ空っぽです。</p>';
                        const cartActions = document.querySelector('.cart-actions');
                        if (cartActions) {
                            cartActions.remove(); // 注文確認ボタンを非表示
                        }
                    }
                }
            })
            .catch(error => console.error('Error fetching cart preview:', error));
    }

    // `app.py` に `/get_cart_preview` エンドポイントを追加する必要があります
    // （ここではJSのみ提示）

    // カートアイテムの数量更新ボタンの処理 (confirm.html)
    document.querySelectorAll('.update-quantity-button').forEach(button => {
        button.addEventListener('click', (event) => {
            const productId = event.target.dataset.id;
            const action = event.target.dataset.action;
            const quantityInput = document.querySelector(`.cart-quantity-input[data-id="${productId}"]`);
            let currentQuantity = parseInt(quantityInput.value);

            if (action === 'minus') {
                if (currentQuantity > 1) {
                    currentQuantity--;
                }
            } else if (action === 'plus') {
                currentQuantity++;
            }
            quantityInput.value = currentQuantity;
            updateCartItem(productId, currentQuantity);
        });
    });

    // カートアイテムの数量入力フィールドの処理 (confirm.html)
    document.querySelectorAll('.cart-quantity-input').forEach(input => {
        input.addEventListener('change', (event) => {
            const productId = event.target.dataset.id;
            let newQuantity = parseInt(event.target.value);
            if (isNaN(newQuantity) || newQuantity < 1) {
                newQuantity = 1; // 最小値は1に
                event.target.value = 1;
            }
            updateCartItem(productId, newQuantity);
        });
    });

    // カートから削除ボタンの処理 (confirm.html)
    document.querySelectorAll('.remove-item-button').forEach(button => {
        button.addEventListener('click', (event) => {
            if (confirm('この商品をカートから削除してもよろしいですか？')) {
                const productId = event.target.dataset.id;
                fetch('/remove_from_cart', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `product_id=${productId}`
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(data.message);
                        location.reload(); // ページをリロードしてカートを更新
                    } else {
                        alert(data.message);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('商品の削除に失敗しました。');
                });
            }
        });
    });

    // カートアイテムの更新処理 (confirm.html)
    function updateCartItem(productId, quantity) {
        fetch('/update_cart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `product_id=${productId}&quantity=${quantity}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 成功したらページをリロードして最新のカート情報を表示
                location.reload();
            } else {
                alert(data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('カートの更新に失敗しました。');
        });
    }

    // index.htmlのカートプレビュー更新のための追加エンドポイント (app.pyに記載する必要あり)
    // Flask側に追加するコード例：
    /*
    @app.route('/get_cart_preview')
    def get_cart_preview():
        return jsonify({'cart': session.get('cart', [])})
    */
    // 上記エンドポイントが追加されたら、DOMContentLoaded時に一度`updateCartPreview()`を呼び出すことで、
    // ページロード時にカートプレビューを正しく表示できます。
    updateCartPreview(); // ページロード時にカートプレビューを初期化
});