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
