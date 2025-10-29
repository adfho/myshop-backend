# API Документация

Базовый URL: `http://localhost:5000/api`

## Аутентификация

Большинство эндпоинтов требуют JWT-токен в заголовке:
```
Authorization: Bearer <token>
```

---

## 🔐 Авторизация (`/api/auth`)

### POST `/api/auth/register`
Регистрация нового пользователя.

**Формат запроса:** `multipart/form-data`

**Поля:**
- `first_name` (обязательно) - Имя пользователя
- `last_name` (обязательно) - Фамилия пользователя
- `email` (обязательно) - Email (валидный формат)
- `password` (обязательно) - Пароль (минимум 6 символов)
- `avatar` (опционально) - Файл изображения (png, jpg, jpeg, до 2MB)

**Пример запроса:**
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -F "first_name=Иван" \
  -F "last_name=Иванов" \
  -F "email=ivan@example.com" \
  -F "password=password123" \
  -F "avatar=@avatar.jpg"
```

**Ответ (201):**
```json
{
  "msg": "User created",
  "user_id": 1
}
```

**Ошибки:**
- `400` - Недостающие поля или невалидные данные
- `409` - Пользователь с таким email уже существует

---

### POST `/api/auth/login`
Вход в систему и получение JWT-токена.

**Формат запроса:** `application/json`

**Тело запроса:**
```json
{
  "email": "ivan@example.com",
  "password": "password123"
}
```

**Пример запроса:**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ivan@example.com","password":"password123"}'
```

**Ответ (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "first_name": "Иван",
    "last_name": "Иванов",
    "email": "ivan@example.com",
    "avatar": "static/avatars/abc123_avatar.jpg"
  }
}
```

**Ошибки:**
- `400` - Недостающие поля или невалидный email
- `401` - Неверный email или пароль

---

### GET `/api/auth/me`
Получение информации о текущем пользователе.

**Требуется авторизация:** Да

**Пример запроса:**
```bash
curl -X GET http://localhost:5000/api/auth/me \
  -H "Authorization: Bearer <token>"
```

**Ответ (200):**
```json
{
  "id": 1,
  "first_name": "Иван",
  "last_name": "Иванов",
  "email": "ivan@example.com",
  "avatar": "static/avatars/abc123_avatar.jpg",
  "unread_notifications": 2
}
```

**Ошибки:**
- `401` - Токен не предоставлен или невалиден
- `404` - Пользователь не найден

---

### GET `/api/auth/notifications`
Получение списка уведомлений пользователя.

**Требуется авторизация:** Да

**Параметры запроса:**
- `unread_only` (опционально) - Если `true`, возвращает только непрочитанные уведомления
- `limit` (опционально) - Максимальное количество уведомлений (по умолчанию: 50)

**Пример запроса:**
```bash
curl -X GET "http://localhost:5000/api/auth/notifications?unread_only=true&limit=10" \
  -H "Authorization: Bearer <token>"
```

**Ответ (200):**
```json
[
  {
    "id": 1,
    "title": "Заказ создан",
    "message": "Ваш заказ #5 на сумму 1234.50 успешно создан",
    "type": "success",
    "is_read": false,
    "created_at": "2024-01-15T10:30:00"
  }
]
```

---

### PUT `/api/auth/notifications/<notification_id>/read`
Отметить уведомление как прочитанное.

**Требуется авторизация:** Да

**Пример запроса:**
```bash
curl -X PUT http://localhost:5000/api/auth/notifications/1/read \
  -H "Authorization: Bearer <token>"
```

**Ответ (200):**
```json
{
  "msg": "Notification marked as read"
}
```

---

### PUT `/api/auth/notifications/read-all`
Отметить все уведомления как прочитанные.

**Требуется авторизация:** Да

**Пример запроса:**
```bash
curl -X PUT http://localhost:5000/api/auth/notifications/read-all \
  -H "Authorization: Bearer <token>"
```

**Ответ (200):**
```json
{
  "msg": "All notifications marked as read"
}
```

---

### GET `/api/auth/avatar/<filename>`
Получение файла аватара пользователя.

**Пример запроса:**
```bash
curl -X GET http://localhost:5000/api/auth/avatar/abc123_avatar.jpg
```

---

## 📦 Каталог (`/api/catalog`)

### GET `/api/catalog/products`
Получение списка товаров с фильтрацией и сортировкой.

**Параметры запроса:**
- `q` (опционально) - Поисковый запрос (по названию товара)
- `category` (опционально) - ID категории для фильтрации
- `min_price` (опционально) - Минимальная цена
- `max_price` (опционально) - Максимальная цена
- `sort` (опционально) - Сортировка: `price_asc`, `price_desc`, `title_asc`, `title_desc`, `id_desc` (по умолчанию)
- `page` (опционально) - Номер страницы (по умолчанию: 1)
- `per_page` (опционально) - Товаров на странице (по умолчанию: 12)

**Пример запроса:**
```bash
curl -X GET "http://localhost:5000/api/catalog/products?category=1&min_price=100&max_price=500&sort=price_asc&page=1"
```

**Ответ (200):**
```json
{
  "items": [
    {
      "id": 1,
      "title": "Smartphone",
      "description": "Good phone",
      "price": 299.99,
      "stock": 10,
      "image": null,
      "category_id": 1
    }
  ],
  "total": 15,
  "page": 1,
  "pages": 2
}
```

---

### GET `/api/catalog/categories`
Получение списка всех категорий.

**Пример запроса:**
```bash
curl -X GET http://localhost:5000/api/catalog/categories
```

**Ответ (200):**
```json
[
  {
    "id": 1,
    "name": "Electronics"
  },
  {
    "id": 2,
    "name": "Books"
  }
]
```

---

### GET `/api/catalog/products/<product_id>`
Получение детальной информации о товаре.

**Пример запроса:**
```bash
curl -X GET http://localhost:5000/api/catalog/products/1
```

**Ответ (200):**
```json
{
  "id": 1,
  "title": "Smartphone",
  "description": "Good phone",
  "price": 299.99,
  "stock": 10,
  "image": null,
  "category_id": 1
}
```

**Ошибки:**
- `404` - Товар не найден

---

## 🛒 Корзина (`/api/cart`)

Корзина сохраняется в Cookies, поэтому запросы должны поддерживать cookies.

### GET `/api/cart/`
Получение содержимого корзины.

**Пример запроса:**
```bash
curl -X GET http://localhost:5000/api/cart/ \
  -b cookies.txt
```

**Ответ (200):**
```json
{
  "items": [
    {
      "product_id": 1,
      "title": "Smartphone",
      "price": 299.99,
      "quantity": 2,
      "line_total": 599.98
    }
  ],
  "subtotal": 599.98,
  "total": 599.98,
  "count": 2
}
```

---

### POST `/api/cart/add`
Добавление товара в корзину.

**Формат запроса:** `application/json`

**Тело запроса:**
```json
{
  "product_id": 1,
  "quantity": 2
}
```

**Пример запроса:**
```bash
curl -X POST http://localhost:5000/api/cart/add \
  -H "Content-Type: application/json" \
  -d '{"product_id":1,"quantity":2}' \
  -c cookies.txt
```

**Ответ (200):**
```json
{
  "items": [...],
  "subtotal": 599.98,
  "total": 599.98,
  "count": 2
}
```

**Ошибки:**
- `400` - Недостающие поля или невалидные данные
- `404` - Товар не найден

---

### POST `/api/cart/remove`
Удаление товара из корзины.

**Формат запроса:** `application/json`

**Тело запроса:**
```json
{
  "product_id": 1
}
```

**Пример запроса:**
```bash
curl -X POST http://localhost:5000/api/cart/remove \
  -H "Content-Type: application/json" \
  -d '{"product_id":1}' \
  -c cookies.txt
```

**Ошибки:**
- `400` - Недостающие поля или невалидные данные

---

### POST `/api/cart/update`
Обновление количества товара в корзине.

**Формат запроса:** `application/json`

**Тело запроса:**
```json
{
  "product_id": 1,
  "quantity": 3
}
```

**Пример запроса:**
```bash
curl -X POST http://localhost:5000/api/cart/update \
  -H "Content-Type: application/json" \
  -d '{"product_id":1,"quantity":3}' \
  -c cookies.txt
```

**Примечание:** Если `quantity` равно 0 или меньше, товар удаляется из корзины.

**Ошибки:**
- `400` - Недостающие поля или невалидные данные
- `404` - Товар не найден

---

## 📋 Заказы (`/api/orders`)

### POST `/api/orders/create`
Создание заказа из текущей корзины.

**Требуется авторизация:** Да

**Пример запроса:**
```bash
curl -X POST http://localhost:5000/api/orders/create \
  -H "Authorization: Bearer <token>" \
  -c cookies.txt
```

**Ответ (201):**
```json
{
  "msg": "Order created",
  "order_id": 5
}
```

**Примечание:** 
- Заказ создается из товаров в корзине (cookie)
- После создания заказа корзина автоматически очищается
- Автоматически создается уведомление о создании заказа

**Ошибки:**
- `400` - Корзина пуста или нет валидных товаров
- `401` - Требуется авторизация
- `404` - Пользователь не найден

---

### GET `/api/orders/my`
Получение истории заказов текущего пользователя.

**Требуется авторизация:** Да

**Пример запроса:**
```bash
curl -X GET http://localhost:5000/api/orders/my \
  -H "Authorization: Bearer <token>"
```

**Ответ (200):**
```json
[
  {
    "id": 5,
    "created_at": "2024-01-15T10:30:00",
    "total": 1234.50,
    "status": "created",
    "items": [
      {
        "product_id": 1,
        "title": "Smartphone",
        "quantity": 2,
        "price": 299.99
      }
    ]
  }
]
```

**Примечание:** Заказы отсортированы по дате создания (от новых к старым).

**Ошибки:**
- `401` - Требуется авторизация

---

## Коды статусов HTTP

- `200` - Успешный запрос
- `201` - Ресурс создан
- `400` - Ошибка валидации данных
- `401` - Требуется авторизация или невалидный токен
- `404` - Ресурс не найден
- `409` - Конфликт (например, пользователь уже существует)

---

## Примеры использования с фронтендом

### JavaScript (fetch)

```javascript
// Вход
const loginResponse = await fetch('http://localhost:5000/api/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'ivan@example.com',
    password: 'password123'
  })
});

const { access_token, user } = await loginResponse.json();

// Получение данных пользователя
const meResponse = await fetch('http://localhost:5000/api/auth/me', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  },
  credentials: 'include' // важно для cookies
});

// Добавление в корзину
await fetch('http://localhost:5000/api/cart/add', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    product_id: 1,
    quantity: 2
  }),
  credentials: 'include' // важно для cookies
});
```

