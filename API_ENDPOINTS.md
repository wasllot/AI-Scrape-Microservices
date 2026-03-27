# Guía de API para el Frontend (Producción)

Esta guía detalla las URLs de producción **completas y reales** necesarias para conectar tu aplicación Frontend (React, Vue, Móvil, etc.) al *Business Core* alojado en `api.reinaldotineo.online`.

**Dominio de Producción:** `https://api.reinaldotineo.online`
*(Nota: Asumimos `https` si tienes un certificado SSL configurado, de lo contrario utilícese `http`)*

---

## 1. Autenticación (Auth)
Estos endpoints son públicos.

*   **Registro de Usuario**
    *   **Método:** `POST`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/auth/register`
    *   **Payload (Body JSON):** `{ "name": "Usuario", "email": "user@test.com", "password": "password" }`
    *   **Respuesta Exitosa:** Devuelve un token JWT.

*   **Inicio de Sesión (Login)**
    *   **Método:** `POST`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/auth/login`
    *   **Payload (Body JSON):** `{ "email": "user@test.com", "password": "password" }`
    *   **Respuesta Exitosa:** `{"access_token": "eyJhbG...", "token_type": "bearer", "expires_in": 3600}`

> [!IMPORTANT]
> Guarda el `access_token` en tu LocalStorage o Cookies para enviarlo en los **Headers** de las rutas protegidas a continuación.

---

## 2. Catálogo (Público)
Endpoints utilizados para pintar la página de inicio, detalles de productos y categorías. No requieren Token.

*   **Listar Todos los Productos:** 
    *   **Método:** `GET`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/products`
*   **Listar Productos Destacados:** 
    *   **Método:** `GET`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/products/featured`
*   **Obtener Detalle de un Producto (por ID):** 
    *   **Método:** `GET`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/products/{id}`

*   **Listar Todas las Categorías:** 
    *   **Método:** `GET`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/categories`
*   **Obtener Filtros de Búsqueda Activos:** 
    *   **Método:** `GET`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/search/filters`

*   **Listar Tiendas Oficiales/Vendedores:** 
    *   **Método:** `GET`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/stores`
*   **Obtener Detalle de Tienda (por SLUG o ID):** 
    *   **Método:** `GET`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/stores/{id}`

---

## 3. Funciones de Compra (Protegidas)
Para que los clientes puedan añadir items al carrito o pagar, el Frontend debe incluir siempre este Header en la petición:
**Header Requerido:** `Authorization: Bearer <tu_token_aqui>`

### Carrito de Compras
*   **Ver el Carrito Actual del Usuario Logueado (Devuelve total a pagar, items e impuestos):**
    *   **Método:** `GET`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/cart`
*   **Añadir un Producto al Carrito:**
    *   **Método:** `POST`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/cart/items`
    *   **Payload (Body JSON):** `{ "product_id": 1, "product_variant_id": null, "quantity": 1 }`
*   **Actualizar Cantidad de un Item (Ej. Subir a 2 unidades):**
    *   **Método:** `PUT`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/cart/items/{item_id}`
    *   **Payload (Body JSON):** `{ "quantity": 2 }`
*   **Eliminar un Producto del Carrito:**
    *   **Método:** `DELETE`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/cart/items/{item_id}`
*   **Vaciar Completamente el Carrito (Flush):**
    *   **Método:** `DELETE`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/cart`

### Órdenes y Checkout
*   **Procesar Pago y Finalizar Compra (Convierte el Carrito en una Orden):**
    *   **Método:** `POST`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/orders`
    *   **Payload (Opcional):** `{ "shipping_address_id": 1, "billing_address_id": 1, "payment_method": "stripe", "notes": "Dejar caja en portería" }`
*   **Ver el Historial de Órdenes del Usuario:**
    *   **Método:** `GET`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/orders`
*   **Rastrear Estado de Envío de una Orden:**
    *   **Método:** `GET`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/orders/{order_id}/track`

---

## 4. Perfil de Usuario (Protegido)
**Header Requerido:** `Authorization: Bearer <tu_token_aqui>`

*   **Ver datos Básicos de Perfil ("Mi Cuenta"):**
    *   **Método:** `GET`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/user`  (O `/api/v1/user/profile` dependiendo del Frontend, el endpoint devuelve los datos del `$user` de Auth)
*   **Editar Perfil (Por ejemplo: cambiar Nombre o Teléfono):**
    *   **Método:** `PUT`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/user/profile`
    *   **Payload (Body JSON):** `{ "name": "Nuevo Nombre", "phone": "+584141234567" }`

*   **Ver Lista de Deseos (Favoritos / Wishlist):**
    *   **Método:** `GET`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/wishlist`
*   **Añadir un Producto a Favoritos:**
    *   **Método:** `POST`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/wishlist`
    *   **Payload (Body JSON):** `{ "product_id": 1 }`

---

## 5. Multimedia (Archivos con R2)
**Header Requerido:** `Authorization: Bearer <tu_token_aqui>`

Para que el backend sea más rápido, todas las imágenes se suben primero a este endpoint, y **luego** se envía la URL devuelta (String) cuando se cree un Producto, Categoría o Perfil.

*   **Subir una nueva Imagen O Logo:**
    *   **Método:** `POST`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/upload/image`
    *   **Payload (Form-Data `multipart/form-data`):** 
        *   `image`: [El archivo físico `File/Blob`]
        *   `folder`: `"products"` (Opciones válidas: `products`, `categories`, `sellers`, `avatars`)
    *   **Respuesta Exitosa:**
        ```json
        {
            "success": true,
            "data": {
                "path": "products/1234_1234.jpg",
                "url": "https://pub-xxxx.r2.dev/products/1234_1234.jpg"
            }
        }
        ```
    *   **Paso Siguiente:** Copia el campo `.url` devuelto, y úsalo en tu siguiente `POST /api/v1/products` en el campo "image" o similar.

---

## 6. Dashboard de Vendedor (Protegido — Rol Seller)
**Header Requerido:** `Authorization: Bearer <token_del_vendedor>`

### Perfil de la Tienda
*   **Ver datos de mi Tienda:**
    *   **Método:** `GET`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/sellers/me`
*   **Actualizar datos de mi Tienda:**
    *   **Método:** `PUT`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/sellers/me`
    *   **Payload (Body JSON):**
        ```json
        {
          "store_name": "Mi Tienda",
          "description": "Descripción de la tienda",
          "logo": "https://r2.dev/logo.png",
          "banner": "https://r2.dev/banner.png",
          "whatsapp": "+584141234567",
          "contact_email": "tienda@example.com",
          "website": "https://mitienda.com",
          "address": "Av. Principal, Local 1",
          "categories": [1, 3],
          "bank_account": "0105-...",
          "bank_name": "Banco de Venezuela"
        }
        ```

### Gestión de Productos (Solo los de la tienda propia)
*   **Listar mis Productos:**
    *   **Método:** `GET`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/sellers/me/products`
    *   **Query Params Opcionales:** `?search=laptop&is_active=true&per_page=20`
*   **Crear un Producto en mi Tienda:**
    *   **Método:** `POST`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/sellers/me/products`
    *   **Payload (Body JSON):** `{ "name": "Laptop Pro", "price": 999.99, "stock_quantity": 10, "category_id": 1 }`
*   **Actualizar un Producto:**
    *   **Método:** `PUT`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/sellers/me/products/{id}`
    *   **Payload (Body JSON):** `{ "price": 849.99, "stock_quantity": 5, "is_active": true }`
*   **Eliminar un Producto:**
    *   **Método:** `DELETE`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/sellers/me/products/{id}`

---

## 7. Panel de Administración (Protegido — Rol Admin)
**Header Requerido:** `Authorization: Bearer <token_del_admin>`

> [!IMPORTANT]
> Todos estos endpoints responden con `403 Forbidden` si el token no pertenece a un usuario de rol `admin`.

### Gestión de Tiendas
*   **Listar Todas las Tiendas (con filtros):**
    *   **Método:** `GET`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/admin/stores`
    *   **Query Params:** `?status=pending&search=tienda&category=1&per_page=20`
*   **Ver Detalle de una Tienda:**
    *   **Método:** `GET`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/admin/stores/{id}`
*   **Crear una Tienda (con nuevo usuario Vendedor):**
    *   **Método:** `POST`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/admin/stores`
    *   **Payload (Body JSON):**
        ```json
        {
          "store_name": "Nueva Tienda Oficial",
          "description": "Descripción...",
          "logo": "https://r2.dev/logo.png",
          "categories": [1, 2],
          "whatsapp": "+584141234567",
          "contact_email": "contacto@tienda.com",
          "user_name": "Juan Pérez",
          "user_email": "juan@tienda.com",
          "user_password": "password123"
        }
        ```
*   **Editar cualquier Tienda:**
    *   **Método:** `PUT`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/admin/stores/{id}`
    *   **Payload:** Cualquier campo de la tienda, incluyendo `status: "suspended"`.
*   **Eliminar una Tienda:**
    *   **Método:** `DELETE`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/admin/stores/{id}`
*   **Aprobar Tienda Pendiente:**
    *   **Método:** `POST`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/admin/stores/{id}/approve`
*   **🔑 Impersonar / Logearse como Tienda:**
    *   **Método:** `POST`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/admin/stores/{id}/impersonate`
    *   **Respuesta:** Devuelve un `access_token` JWT del usuario vendedor de esa tienda. El frontend puede usar ese token para acceder al dashboard de la tienda directamente.

### Gestión de Productos (Cualquier Tienda)
*   **Listar Todos los Productos (con filtros):**
    *   **Método:** `GET`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/admin/products`
    *   **Query Params:** `?seller_id=3&category_id=1&search=laptop&per_page=30`
*   **Crear Producto para cualquier Tienda:**
    *   **Método:** `POST`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/admin/products`
    *   **Payload:** `{ "seller_id": 3, "name": "Producto", "price": 99.99, "stock_quantity": 50 }`
*   **Actualizar cualquier Producto:**
    *   **Método:** `PUT`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/admin/products/{id}`
*   **Eliminar cualquier Producto:**
    *   **Método:** `DELETE`
    *   **URL Completa:** `https://api.reinaldotineo.online/api/v1/admin/products/{id}`

