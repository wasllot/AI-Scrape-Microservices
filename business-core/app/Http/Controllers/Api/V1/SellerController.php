<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;

/**
 * @OA\Tag(
 *     name="Sellers",
 *     description="Gestión de vendedores"
 * )
 */
class SellerController extends Controller
{
    /**
     * @OA\Get(
     *     path="/api/v1/sellers",
     *     tags={"Sellers"},
     *     summary="Listar vendedores",
     *     description="Obtiene lista de vendedores aprobados",
     *     @OA\Parameter(name="per_page", in="query", required=false, @OA\Schema(type="integer", default=20)),
     *     @OA\Response(response=200, description="Lista de vendedores")
     * )
     */
    public function index(Request $request)
    {
        $sellers = \App\Models\Seller::where('status', 'approved')
            ->with('user:id,name,avatar')
            ->orderBy('rating', 'desc')
            ->paginate($request->per_page ?? 20);

        return response()->json(['success' => true, 'data' => $sellers]);
    }

    /**
     * @OA\Get(
     *     path="/api/v1/sellers/{id}",
     *     tags={"Sellers"},
     *     summary="Ver vendedor",
     *     description="Obtiene los detalles de un vendedor",
     *     @OA\Parameter(name="id", in="path", required=true, @OA\Schema(type="integer")),
     *     @OA\Response(response=200, description="Vendedor encontrado"),
     *     @OA\Response(response=404, description="Vendedor no encontrado")
     * )
     */
    public function show(int $id)
    {
        $seller = \App\Models\Seller::where('status', 'approved')
            ->with('user:id,name,avatar')
            ->findOrFail($id);

        $seller->loadCount(['products' => function ($q) {
            $q->where('is_active', true);
        }]);

        return response()->json(['success' => true, 'data' => $seller]);
    }

    /**
     * @OA\Post(
     *     path="/api/v1/sellers/apply",
     *     tags={"Sellers"},
     *     summary="Solicitar ser vendedor",
     *     description="Envía una solicitud para convertirse en vendedor",
     *     security={{"bearerAuth":{}}},
     *     @OA\RequestBody(
     *         required=true,
     *         @OA\JsonContent(
     *             required={"store_name"},
     *             @OA\Property(property="store_name", type="string", example="Mi Tienda"),
     *             @OA\Property(property="description", type="string", example="Tienda de productos tecnológicos"),
     *             @OA\Property(property="rut", type="string", example="J-12345678-9"),
     *             @OA\Property(property="bank_account", type="string", example="0105-1234-5678-9012"),
     *             @OA\Property(property="bank_name", type="string", example="Banco de Venezuela")
     *         )
     *     ),
     *     @OA\Response(response=201, description="Solicitud enviada"),
     *     @OA\Response(response=400, description="Ya es vendedor"),
     *     @OA\Response(response=422, description="Validación fallida")
     * )
     */
    public function apply(Request $request)
    {
        $user = $request->user();

        if ($user->isSeller()) {
            return response()->json(['success' => false, 'message' => 'Already a seller'], 400);
        }

        $validator = Validator::make($request->all(), [
            'store_name' => 'required|string|max:255',
            'description' => 'nullable|string',
            'rut' => 'nullable|string|max:50',
            'bank_account' => 'nullable|string',
            'bank_name' => 'nullable|string|max:100',
        ]);

        if ($validator->fails()) {
            return response()->json(['success' => false, 'errors' => $validator->errors()], 422);
        }

        $application = $user->sellerApplication()->create([
            ...$request->all(),
            'status' => 'pending',
        ]);

        return response()->json([
            'success' => true,
            'data' => $application,
            'message' => 'Application submitted successfully'
        ], 201);
    }

    /**
     * @OA\Get(
     *     path="/api/v1/sellers/me",
     *     tags={"Sellers"},
     *     summary="Mi perfil de vendedor",
     *     description="Obtiene el perfil del vendedor actual",
     *     security={{"bearerAuth":{}}},
     *     @OA\Response(response=200, description="Perfil del vendedor"),
     *     @OA\Response(response=404, description="No es vendedor")
     * )
     */
    public function me(Request $request)
    {
        $seller = $request->user()->seller;

        if (!$seller) {
            return response()->json(['success' => false, 'message' => 'Not a seller'], 404);
        }

        $seller->load(['user:id,name,email,phone,avatar']);

        return response()->json(['success' => true, 'data' => $seller]);
    }

    /**
     * @OA\Put(
     *     path="/api/v1/sellers/me",
     *     tags={"Sellers"},
     *     summary="Actualizar perfil",
     *     description="Actualiza el perfil del vendedor",
     *     security={{"bearerAuth":{}}},
     *     @OA\RequestBody(
     *         @OA\JsonContent(
     *             @OA\Property(property="store_name", type="string"),
     *             @OA\Property(property="description", type="string"),
     *             @OA\Property(property="logo", type="string"),
     *             @OA\Property(property="banner", type="string"),
     *             @OA\Property(property="bank_account", type="string"),
     *             @OA\Property(property="bank_name", type="string")
     *         )
     *     ),
     *     @OA\Response(response=200, description="Perfil actualizado"),
     *     @OA\Response(response=404, description="No es vendedor")
     * )
     */
    public function update(Request $request)
    {
        $seller = $request->user()->seller;

        if (!$seller) {
            return response()->json(['success' => false, 'message' => 'Not a seller'], 404);
        }

        $validator = Validator::make($request->all(), [
            'store_name' => 'sometimes|string|max:255',
            'description' => 'nullable|string',
            'logo' => 'nullable|string',
            'banner' => 'nullable|string',
            'bank_account' => 'nullable|string',
            'bank_name' => 'nullable|string|max:100',
        ]);

        if ($validator->fails()) {
            return response()->json(['success' => false, 'errors' => $validator->errors()], 422);
        }

        $seller->update($request->all());

        return response()->json(['success' => true, 'data' => $seller]);
    }
}

