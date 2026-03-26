<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;

/**
 * @OA\Tag(
 *     name="Products",
 *     description="Gestión de productos del marketplace"
 * )
 */
class ProductController extends Controller
{
    /**
     * @OA\Get(
     *     path="/api/v1/products",
     *     tags={"Products"},
     *     summary="Listar productos",
     *     description="Obtiene una lista de productos con paginación",
     *     @OA\Parameter(name="category_id", in="query", required=false, @OA\Schema(type="integer")),
     *     @OA\Parameter(name="seller_id", in="query", required=false, @OA\Schema(type="integer")),
     *     @OA\Parameter(name="source", in="query", required=false, @OA\Schema(type="string", enum={"own", "mercadolibre"})),
     *     @OA\Parameter(name="search", in="query", required=false, @OA\Schema(type="string")),
     *     @OA\Parameter(name="per_page", in="query", required=false, @OA\Schema(type="integer", default=20)),
     *     @OA\Response(response=200, description="Lista de productos")
     * )
     */
    public function index(Request $request)
    {
        $query = \App\Models\Product::with(['seller', 'category', 'images'])
            ->active()
            ->when($request->category ?? $request->category_id, fn($q, $cat) => $q->where('category_id', $cat))
            ->when($request->subcategory, fn($q, $sub) => $q->where('subcategory_id', $sub))
            ->when($request->brand ?? $request->seller_id, fn($q, $brand) => is_numeric($brand) ? $q->where('seller_id', $brand) : $q->whereHas('seller', fn($sq) => $sq->where('slug', $brand)->orWhere('name', 'like', "%{$brand}%")))
            ->when($request->condition, fn($q, $cond) => $q->where('condition', $cond))
            ->when($request->minPrice, fn($q, $min) => $q->where('price', '>=', $min))
            ->when($request->maxPrice, fn($q, $max) => $q->where('price', '<=', $max))
            ->when($request->inStock === 'true' || $request->inStock === '1', fn($q) => $q->where('stock_quantity', '>', 0))
            ->when($request->source, fn($q, $source) => $q->where('source', $source))
            ->when($request->query('query') ?? $request->search, fn($q, $search) => $q->where('name', 'like', "%{$search}%")->orWhere('description', 'like', "%{$search}%"));

        $sort = $request->sort ?? 'newest';
        match ($sort) {
            'featured' => $query->where('is_featured', true)->orderBy('created_at', 'desc'),
            'price_asc' => $query->orderBy('price', 'asc'),
            'price_desc' => $query->orderBy('price', 'desc'),
            'rating' => $query->orderBy('created_at', 'desc'), // Asumir rating si no hay columna
            default => $query->orderBy('created_at', 'desc'),
        };

        $limit = $request->limit ?? $request->per_page ?? 20;
        $products = $query->paginate($limit);

        return response()->json([
            'success' => true,
            'data' => $products->items(),
            'total' => $products->total(),
            'page' => $products->currentPage(),
            'totalPages' => $products->lastPage(),
        ]);
    }

    /**
     * @OA\Get(
     *     path="/api/v1/products/{id}",
     *     tags={"Products"},
     *     summary="Ver producto",
     *     description="Obtiene los detalles de un producto",
     *     @OA\Parameter(name="id", in="path", required=true, @OA\Schema(type="integer")),
     *     @OA\Response(response=200, description="Producto encontrado"),
     *     @OA\Response(response=404, description="Producto no encontrado")
     * )
     */
    public function show(int $id)
    {
        $product = \App\Models\Product::with(['seller', 'category', 'images', 'variants'])
            ->findOrFail($id);

        $product->increment('views');

        return response()->json([
            'success' => true,
            'data' => $product
        ]);
    }

    /**
     * @OA\Post(
     *     path="/api/v1/products",
     *     tags={"Products"},
     *     summary="Crear producto",
     *     description="Crea un nuevo producto (requiere ser vendedor aprobado)",
     *     security={{"bearerAuth":{}}},
     *     @OA\RequestBody(
     *         required=true,
     *         @OA\JsonContent(
     *             required={"name", "price", "stock_quantity"},
     *             @OA\Property(property="name", type="string", example="Producto ejemplo"),
     *             @OA\Property(property="description", type="string", example="Descripción del producto"),
     *             @OA\Property(property="category_id", type="integer", example=1),
     *             @OA\Property(property="price", type="number", example=99.99),
     *             @OA\Property(property="cost_price", type="number", example=50.00),
     *             @OA\Property(property="compare_price", type="number", example=129.99),
     *             @OA\Property(property="stock_quantity", type="integer", example=100),
     *             @OA\Property(property="sku", type="string", example="SKU-001"),
     *             @OA\Property(property="is_active", type="boolean", example=true),
     *             @OA\Property(property="is_featured", type="boolean", example=false)
     *         )
     *     ),
     *     @OA\Response(response=201, description="Producto creado"),
     *     @OA\Response(response=403, description="No autorizado"),
     *     @OA\Response(response=422, description="Validación fallida")
     * )
     */
    public function store(Request $request)
    {
        $user = $request->user();
        
        if (!$user->isSeller() && !$user->isAdmin()) {
            return response()->json(['success' => false, 'message' => 'Unauthorized'], 403);
        }

        $seller = $user->seller;
        
        if (!$seller || !$seller->isApproved()) {
            return response()->json(['success' => false, 'message' => 'Seller not approved'], 403);
        }

        $validated = $request->validate([
            'name' => 'required|string|max:255',
            'description' => 'nullable|string',
            'category_id' => 'nullable|exists:categories,id',
            'price' => 'required|numeric|min:0',
            'cost_price' => 'nullable|numeric|min:0',
            'compare_price' => 'nullable|numeric|min:0',
            'stock_quantity' => 'required|integer|min:0',
            'sku' => 'nullable|string|unique:products',
            'is_active' => 'boolean',
            'is_featured' => 'boolean',
        ]);

        $product = $seller->products()->create([
            ...$validated,
            'slug' => \Illuminate\Support\Str::slug($validated['name']),
            'source' => 'own',
        ]);

        return response()->json([
            'success' => true,
            'data' => $product,
            'message' => 'Product created successfully'
        ], 201);
    }

    /**
     * @OA\Put(
     *     path="/api/v1/products/{id}",
     *     tags={"Products"},
     *     summary="Actualizar producto",
     *     description="Actualiza un producto existente",
     *     security={{"bearerAuth":{}}},
     *     @OA\Parameter(name="id", in="path", required=true, @OA\Schema(type="integer")),
     *     @OA\RequestBody(
     *         @OA\JsonContent(
     *             @OA\Property(property="name", type="string"),
     *             @OA\Property(property="description", type="string"),
     *             @OA\Property(property="price", type="number"),
     *             @OA\Property(property="stock_quantity", type="integer"),
     *             @OA\Property(property="is_active", type="boolean")
     *         )
     *     ),
     *     @OA\Response(response=200, description="Producto actualizado"),
     *     @OA\Response(response=403, description="No autorizado"),
     *     @OA\Response(response=404, description="Producto no encontrado")
     * )
     */
    public function update(Request $request, int $id)
    {
        $user = $request->user();
        $product = \App\Models\Product::findOrFail($id);

        if (!$user->canManageProducts()) {
            return response()->json(['success' => false, 'message' => 'Unauthorized'], 403);
        }

        if ($user->isSeller() && $product->seller_id !== $user->seller->id) {
            return response()->json(['success' => false, 'message' => 'Unauthorized'], 403);
        }

        $validated = $request->validate([
            'name' => 'sometimes|string|max:255',
            'description' => 'nullable|string',
            'category_id' => 'nullable|exists:categories,id',
            'price' => 'sometimes|numeric|min:0',
            'cost_price' => 'nullable|numeric|min:0',
            'compare_price' => 'nullable|numeric|min:0',
            'stock_quantity' => 'sometimes|integer|min:0',
            'sku' => 'sometimes|string|unique:products,sku,' . $id,
            'is_active' => 'sometimes|boolean',
            'is_featured' => 'sometimes|boolean',
        ]);

        $product->update($validated);

        return response()->json([
            'success' => true,
            'data' => $product,
            'message' => 'Product updated successfully'
        ]);
    }

    /**
     * @OA\Delete(
     *     path="/api/v1/products/{id}",
     *     tags={"Products"},
     *     summary="Eliminar producto",
     *     description="Elimina un producto",
     *     security={{"bearerAuth":{}}},
     *     @OA\Parameter(name="id", in="path", required=true, @OA\Schema(type="integer")),
     *     @OA\Response(response=200, description="Producto eliminado"),
     *     @OA\Response(response=403, description="No autorizado"),
     *     @OA\Response(response=404, description="Producto no encontrado")
     * )
     */
    public function destroy(Request $request, int $id)
    {
        $user = $request->user();
        $product = \App\Models\Product::findOrFail($id);

        if ($user->isSeller() && $product->seller_id !== $user->seller->id) {
            return response()->json(['success' => false, 'message' => 'Unauthorized'], 403);
        }

        $product->delete();

        return response()->json([
            'success' => true,
            'message' => 'Product deleted successfully'
        ]);
    }

    /**
     * @OA\Get(
     *     path="/api/v1/products/featured",
     *     tags={"Products"},
     *     summary="Productos destacados",
     *     description="Obtiene productos destacados",
     *     @OA\Response(response=200, description="Lista de productos destacados")
     * )
     */
    public function featured()
    {
        $products = \App\Models\Product::with(['seller', 'images'])
            ->active()
            ->featured()
            ->take(10)
            ->get();

        return response()->json([
            'success' => true,
            'data' => $products
        ]);
    }
}
