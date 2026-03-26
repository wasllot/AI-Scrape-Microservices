<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;

/**
 * @OA\Tag(
 *     name="Orders",
 *     description="Gestión de pedidos"
 * )
 */
class OrderController extends Controller
{
    /**
     * @OA\Get(
     *     path="/api/v1/orders",
     *     tags={"Orders"},
     *     summary="Listar pedidos",
     *     description="Obtiene los pedidos del usuario actual",
     *     security={{"bearerAuth":{}}},
     *     @OA\Parameter(name="per_page", in="query", required=false, @OA\Schema(type="integer", default=20)),
     *     @OA\Response(response=200, description="Lista de pedidos")
     * )
     */
    public function index(Request $request)
    {
        $orders = $request->user()->orders()
            ->with(['items', 'seller'])
            ->orderBy('created_at', 'desc')
            ->paginate($request->per_page ?? 20);

        return response()->json(['success' => true, 'data' => $orders]);
    }

    /**
     * @OA\Get(
     *     path="/api/v1/orders/{id}",
     *     tags={"Orders"},
     *     summary="Ver pedido",
     *     description="Obtiene los detalles de un pedido",
     *     security={{"bearerAuth":{}}},
     *     @OA\Parameter(name="id", in="path", required=true, @OA\Schema(type="integer")),
     *     @OA\Response(response=200, description="Pedido encontrado"),
     *     @OA\Response(response=404, description="Pedido no encontrado")
     * )
     */
    public function show(Request $request, int $id)
    {
        $order = $request->user()->orders()
            ->with(['items', 'items.product', 'seller', 'shippingAddress'])
            ->findOrFail($id);

        return response()->json(['success' => true, 'data' => $order]);
    }

    /**
     * @OA\Post(
     *     path="/api/v1/orders",
     *     tags={"Orders"},
     *     summary="Crear pedido (Checkout)",
     *     description="Crea un pedido a partir del carrito",
     *     security={{"bearerAuth":{}}},
     *     @OA\RequestBody(
     *         required=true,
     *         @OA\JsonContent(
     *             required={"shipping_address_id", "payment_method"},
     *             @OA\Property(property="shipping_address_id", type="integer", example=1),
     *             @OA\Property(property="payment_method", type="string", example="transferencia"),
     *             @OA\Property(property="notes", type="string", example="Entregar en la puerta")
     *         )
     *     ),
     *     @OA\Response(response=201, description="Pedido creado"),
     *     @OA\Response(response=400, description="Carrito vacío"),
     *     @OA\Response(response=422, description="Validación fallida")
     * )
     */
    public function store(Request $request)
    {
        $shippingAddressId = $request->input('shippingAddress.id') ?? $request->shipping_address_id;
        $paymentMethod = $request->paymentMethod ?? $request->payment_method;
        
        $request->merge([
            'shipping_address_id' => $shippingAddressId,
            'payment_method' => $paymentMethod
        ]);

        $validator = Validator::make($request->all(), [
            'shipping_address_id' => 'required|exists:addresses,id',
            'payment_method' => 'required|string',
            'notes' => 'nullable|string',
        ]);

        if ($validator->fails()) {
            return response()->json(['success' => false, 'errors' => $validator->errors()], 422);
        }

        $user = $request->user();
        $cart = $user->cart;

        if (!$cart || $cart->items->isEmpty()) {
            return response()->json(['success' => false, 'message' => 'Cart is empty'], 400);
        }

        $address = $user->addresses()->findOrFail($request->shipping_address_id);

        $order = \DB::transaction(function () use ($user, $cart, $request, $address) {
            $order = $user->orders()->create([
                'seller_id' => $cart->items->first()->product->seller_id,
                'shipping_address_id' => $address->id,
                'status' => 'pending',
                'subtotal' => $cart->subtotal,
                'tax' => $cart->tax,
                'shipping_cost' => 0,
                'discount' => 0,
                'total' => $cart->total,
                'currency' => 'VES',
                'payment_method' => $request->payment_method,
                'customer_notes' => $request->notes,
            ]);

            foreach ($cart->items as $item) {
                $order->items()->create([
                    'product_id' => $item->product_id,
                    'product_variant_id' => $item->product_variant_id,
                    'product_name' => $item->product->name,
                    'product_sku' => $item->product->sku,
                    'product_image' => $item->product->images->first()?->url,
                    'quantity' => $item->quantity,
                    'unit_price' => $item->unit_price,
                    'subtotal' => $item->subtotal,
                ]);

                $item->product->decrement('stock_quantity', $item->quantity);
            }

            $cart->items()->delete();
            $cart->recalculate();

            return $order;
        });

        $order->load(['items', 'items.product']);

        return response()->json([
            'success' => true,
            'data' => $order,
            'message' => 'Order created successfully'
        ], 201);
    }

    /**
     * @OA\Get(
     *     path="/api/v1/orders/{id}/track",
     *     tags={"Orders"},
     *     summary="Rastrear pedido",
     *     description="Obtiene el estado y timeline de un pedido",
     *     security={{"bearerAuth":{}}},
     *     @OA\Parameter(name="id", in="path", required=true, @OA\Schema(type="integer")),
     *     @OA\Response(response=200, description="Información de tracking"),
     *     @OA\Response(response=404, description="Pedido no encontrado")
     * )
     */
    public function track(Request $request, int $id)
    {
        $order = $request->user()->orders()
            ->with(['statusHistory'])
            ->findOrFail($id);

        return response()->json([
            'success' => true,
            'data' => [
                'order_number' => $order->order_number,
                'status' => $order->status,
                'tracking_number' => $order->tracking_number,
                'shipped_at' => $order->shipped_at,
                'delivered_at' => $order->delivered_at,
                'timeline' => $order->statusHistory->map(fn($h) => [
                    'status' => $h->status,
                    'comment' => $h->comment,
                    'created_at' => $h->created_at,
                ]),
            ]
        ]);
    }
}
