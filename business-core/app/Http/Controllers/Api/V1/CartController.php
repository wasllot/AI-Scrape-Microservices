<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;

/**
 * @OA\Tag(
 *     name="Cart",
 *     description="Gestión del carrito de compras"
 * )
 */
class CartController extends Controller
{
    /**
     * @OA\Get(
     *     path="/api/v1/cart",
     *     tags={"Cart"},
     *     summary="Ver carrito",
     *     description="Obtiene el carrito del usuario actual",
     *     security={{"bearerAuth":{}}},
     *     @OA\Response(response=200, description="Carrito obtenido"),
     *     @OA\Response(response=401, description="No autenticado")
     * )
     */
    public function index(Request $request)
    {
        $cart = $request->user()->cart()->with(['items.product', 'items.productVariant'])->first();

        if (!$cart) {
            $cart = $request->user()->cart()->create([
                'subtotal' => 0,
                'tax' => 0,
                'total' => 0,
            ]);
        }

        return response()->json([
            'success' => true,
            'data' => $cart
        ]);
    }

    /**
     * @OA\Post(
     *     path="/api/v1/cart/items",
     *     tags={"Cart"},
     *     summary="Agregar item al carrito",
     *     description="Agrega un producto al carrito",
     *     security={{"bearerAuth":{}}},
     *     @OA\RequestBody(
     *         required=true,
     *         @OA\JsonContent(
     *             required={"product_id", "quantity"},
     *             @OA\Property(property="product_id", type="integer", example=1),
     *             @OA\Property(property="quantity", type="integer", example=2),
     *             @OA\Property(property="product_variant_id", type="integer", example=null)
     *         )
     *     ),
     *     @OA\Response(response=200, description="Item agregado"),
     *     @OA\Response(response=400, description="Producto no disponible"),
     *     @OA\Response(response=422, description="Validación fallida")
     * )
     */
    public function addItem(Request $request)
    {
        // Support frontend camelCase
        $productId = $request->productId ?? $request->product_id;
        $request->merge(['product_id' => $productId]);

        $validator = Validator::make($request->all(), [
            'product_id' => 'required|exists:products,id',
            'quantity' => 'required|integer|min:1',
            'product_variant_id' => 'nullable|exists:product_variants,id',
            'size' => 'nullable|string',
            'color' => 'nullable|string',
        ]);

        if ($validator->fails()) {
            return response()->json(['success' => false, 'errors' => $validator->errors()], 422);
        }

        $user = $request->user();
        $product = \App\Models\Product::findOrFail($request->product_id);

        if (!$product->is_active) {
            return response()->json(['success' => false, 'message' => 'Product not available'], 400);
        }

        $cart = $user->cart ?? $user->cart()->create(['subtotal' => 0, 'tax' => 0, 'total' => 0]);

        $price = $product->price;
        
        $cartItem = $cart->items()->where('product_id', $request->product_id)
            ->where('product_variant_id', $request->product_variant_id)
            ->first();

        if ($cartItem) {
            $cartItem->quantity += $request->quantity;
            $cartItem->subtotal = $cartItem->quantity * $cartItem->unit_price;
            $cartItem->save();
        } else {
            $cartItem = $cart->items()->create([
                'product_id' => $request->product_id,
                'product_variant_id' => $request->product_variant_id,
                'quantity' => $request->quantity,
                'unit_price' => $price,
                'subtotal' => $price * $request->quantity,
                // Omitimos size y color a menos que haya columnas, idealmente se manejan vía variant
            ]);
        }

        $cart->recalculate();
        $cart->load(['items.product', 'items.productVariant']);

        return response()->json([
            'success' => true,
            'data' => $cart,
            'message' => 'Item added to cart'
        ]);
    }

    /**
     * @OA\Put(
     *     path="/api/v1/cart/items/{itemId}",
     *     tags={"Cart"},
     *     summary="Actualizar cantidad",
     *     description="Actualiza la cantidad de un item en el carrito",
     *     security={{"bearerAuth":{}}},
     *     @OA\Parameter(name="itemId", in="path", required=true, @OA\Schema(type="integer")),
     *     @OA\RequestBody(
     *         required=true,
     *         @OA\JsonContent(
     *             required={"quantity"},
     *             @OA\Property(property="quantity", type="integer", example=3)
     *         )
     *     ),
     *     @OA\Response(response=200, description="Carrito actualizado"),
     *     @OA\Response(response=404, description="Item no encontrado")
     * )
     */
    public function updateItem(Request $request, int $itemId)
    {
        $validator = Validator::make($request->all(), [
            'quantity' => 'required|integer|min:1',
        ]);

        if ($validator->fails()) {
            return response()->json(['success' => false, 'errors' => $validator->errors()], 422);
        }

        $cart = $request->user()->cart;
        
        if (!$cart) {
            return response()->json(['success' => false, 'message' => 'Cart not found'], 404);
        }

        $cartItem = $cart->items()->findOrFail($itemId);
        $cartItem->quantity = $request->quantity;
        $cartItem->subtotal = $cartItem->unit_price * $request->quantity;
        $cartItem->save();

        $cart->recalculate();
        $cart->load(['items.product', 'items.productVariant']);

        return response()->json([
            'success' => true,
            'data' => $cart,
            'message' => 'Cart updated'
        ]);
    }

    /**
     * @OA\Delete(
     *     path="/api/v1/cart/items/{itemId}",
     *     tags={"Cart"},
     *     summary="Eliminar item",
     *     description="Elimina un item del carrito",
     *     security={{"bearerAuth":{}}},
     *     @OA\Parameter(name="itemId", in="path", required=true, @OA\Schema(type="integer")),
     *     @OA\Response(response=200, description="Item eliminado"),
     *     @OA\Response(response=404, description="Item no encontrado")
     * )
     */
    public function removeItem(Request $request, int $itemId)
    {
        $cart = $request->user()->cart;
        
        if (!$cart) {
            return response()->json(['success' => false, 'message' => 'Cart not found'], 404);
        }

        $cartItem = $cart->items()->findOrFail($itemId);
        $cartItem->delete();

        $cart->recalculate();
        $cart->load(['items.product', 'items.productVariant']);

        return response()->json([
            'success' => true,
            'data' => $cart,
            'message' => 'Item removed from cart'
        ]);
    }

    /**
     * @OA\Delete(
     *     path="/api/v1/cart",
     *     tags={"Cart"},
     *     summary="Vaciar carrito",
     *     description="Elimina todos los items del carrito",
     *     security={{"bearerAuth":{}}},
     *     @OA\Response(response=200, description="Carrito vaciado")
     * )
     */
    public function clear(Request $request)
    {
        $cart = $request->user()->cart;
        
        if ($cart) {
            $cart->items()->delete();
            $cart->recalculate();
        }

        return response()->json([
            'success' => true,
            'message' => 'Cart cleared'
        ]);
    }
}
