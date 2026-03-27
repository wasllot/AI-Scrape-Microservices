<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Models\Seller;
use App\Models\Product;
use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Str;
use PHPOpenSourceSaver\JWTAuth\Facades\JWTAuth;

class AdminController extends Controller
{
    private function requireAdmin(Request $request)
    {
        if (!$request->user()?->isAdmin()) {
            abort(403, 'Admin access required.');
        }
    }

    // ═══════════════════════════════════════════
    // STORE (SELLER) MANAGEMENT
    // ═══════════════════════════════════════════

    /** List all stores with filters */
    public function storeIndex(Request $request)
    {
        $this->requireAdmin($request);

        $query = Seller::with('user:id,name,email,phone,avatar')
            ->withCount('products')
            ->when($request->status, fn($q, $s) => $q->where('status', $s))
            ->when($request->search, fn($q, $s) => $q->where('store_name', 'like', "%{$s}%"))
            ->when($request->category, fn($q, $cat) => $q->whereJsonContains('categories', (int) $cat))
            ->orderBy('created_at', 'desc');

        return response()->json([
            'success' => true,
            'data'    => $query->paginate($request->per_page ?? 20),
        ]);
    }

    /** Get single store */
    public function storeShow(Request $request, int $id)
    {
        $this->requireAdmin($request);
        $seller = Seller::with(['user:id,name,email,phone,avatar', 'products'])->findOrFail($id);
        return response()->json(['success' => true, 'data' => $seller]);
    }

    /** Create store + linked seller user */
    public function storeCreate(Request $request)
    {
        $this->requireAdmin($request);

        $validated = $request->validate([
            'store_name'    => 'required|string|max:255',
            'description'   => 'nullable|string',
            'logo'          => 'nullable|string|url',
            'banner'        => 'nullable|string|url',
            'contact_email' => 'nullable|email',
            'whatsapp'      => 'nullable|string|max:30',
            'website'       => 'nullable|string|url',
            'address'       => 'nullable|string|max:255',
            'categories'    => 'nullable|array',
            'categories.*'  => 'integer',
            // User fields
            'user_name'     => 'required|string|max:100',
            'user_email'    => 'required|email|unique:users,email',
            'user_password' => 'required|string|min:8',
        ]);

        $seller = DB::transaction(function () use ($validated) {
            $user = User::create([
                'name'     => $validated['user_name'],
                'email'    => $validated['user_email'],
                'password' => Hash::make($validated['user_password']),
                'role'     => User::ROLE_SELLER,
            ]);

            return $user->seller()->create([
                'store_name'    => $validated['store_name'],
                'slug'          => Str::slug($validated['store_name']),
                'description'   => $validated['description'] ?? null,
                'logo'          => $validated['logo'] ?? null,
                'banner'        => $validated['banner'] ?? null,
                'contact_email' => $validated['contact_email'] ?? null,
                'whatsapp'      => $validated['whatsapp'] ?? null,
                'website'       => $validated['website'] ?? null,
                'address'       => $validated['address'] ?? null,
                'categories'    => $validated['categories'] ?? null,
                'status'        => 'approved',
                'approved_at'   => now(),
            ]);
        });

        return response()->json(['success' => true, 'data' => $seller, 'message' => 'Store created successfully'], 201);
    }

    /** Update any store */
    public function storeUpdate(Request $request, int $id)
    {
        $this->requireAdmin($request);
        $seller = Seller::findOrFail($id);

        $validated = $request->validate([
            'store_name'    => 'sometimes|string|max:255',
            'description'   => 'nullable|string',
            'logo'          => 'nullable|string',
            'banner'        => 'nullable|string',
            'contact_email' => 'nullable|email',
            'whatsapp'      => 'nullable|string|max:30',
            'website'       => 'nullable|string',
            'address'       => 'nullable|string|max:255',
            'categories'    => 'nullable|array',
            'categories.*'  => 'integer',
            'status'        => 'sometimes|in:pending,approved,rejected,suspended',
            'rejection_reason' => 'nullable|string',
            'commission_rate'  => 'nullable|numeric|min:0|max:100',
        ]);

        if (isset($validated['status']) && $validated['status'] === 'approved' && !$seller->approved_at) {
            $validated['approved_at'] = now();
        }

        $seller->update($validated);

        return response()->json(['success' => true, 'data' => $seller->fresh('user')]);
    }

    /** Delete any store */
    public function storeDelete(Request $request, int $id)
    {
        $this->requireAdmin($request);
        $seller = Seller::findOrFail($id);
        $seller->delete();
        return response()->json(['success' => true, 'message' => 'Store deleted successfully']);
    }

    /** Approve a pending store */
    public function storeApprove(Request $request, int $id)
    {
        $this->requireAdmin($request);
        $seller = Seller::findOrFail($id);
        $seller->update(['status' => 'approved', 'approved_at' => now()]);
        return response()->json(['success' => true, 'data' => $seller, 'message' => 'Store approved']);
    }

    /** Impersonate seller — returns a token for the store owner */
    public function storeImpersonate(Request $request, int $id)
    {
        $this->requireAdmin($request);
        $seller = Seller::with('user')->findOrFail($id);

        if (!$seller->user) {
            return response()->json(['success' => false, 'message' => 'Store has no associated user'], 404);
        }

        $token = JWTAuth::fromUser($seller->user);

        return response()->json([
            'success'    => true,
            'message'    => "Impersonating {$seller->store_name}",
            'data'       => [
                'access_token' => $token,
                'token_type'   => 'bearer',
                'expires_in'   => config('jwt.ttl') * 60,
                'user'         => $seller->user,
                'seller'       => $seller,
            ],
        ]);
    }

    // ═══════════════════════════════════════════
    // PRODUCT MANAGEMENT (ADMIN)
    // ═══════════════════════════════════════════

    /** List all products — optional seller_id filter */
    public function productIndex(Request $request)
    {
        $this->requireAdmin($request);

        $products = Product::with(['seller:id,store_name,slug', 'category:id,name'])
            ->when($request->seller_id, fn($q, $sid) => $q->where('seller_id', $sid))
            ->when($request->category_id, fn($q, $cid) => $q->where('category_id', $cid))
            ->when($request->search, fn($q, $s) => $q->where('name', 'like', "%{$s}%"))
            ->orderBy('created_at', 'desc')
            ->paginate($request->per_page ?? 30);

        return response()->json(['success' => true, 'data' => $products]);
    }

    /** Create a product for any store */
    public function productCreate(Request $request)
    {
        $this->requireAdmin($request);

        $validated = $request->validate([
            'seller_id'      => 'required|exists:sellers,id',
            'name'           => 'required|string|max:255',
            'description'    => 'nullable|string',
            'category_id'    => 'nullable|exists:categories,id',
            'price'          => 'required|numeric|min:0',
            'cost_price'     => 'nullable|numeric|min:0',
            'compare_price'  => 'nullable|numeric|min:0',
            'stock_quantity' => 'required|integer|min:0',
            'sku'            => 'nullable|string|unique:products',
            'is_active'      => 'boolean',
            'is_featured'    => 'boolean',
        ]);

        $product = Product::create([
            ...$validated,
            'slug'   => Str::slug($validated['name']),
            'source' => 'own',
        ]);

        return response()->json(['success' => true, 'data' => $product, 'message' => 'Product created'], 201);
    }

    /** Update any product */
    public function productUpdate(Request $request, int $id)
    {
        $this->requireAdmin($request);
        $product = Product::findOrFail($id);

        $validated = $request->validate([
            'name'           => 'sometimes|string|max:255',
            'description'    => 'nullable|string',
            'category_id'    => 'nullable|exists:categories,id',
            'price'          => 'sometimes|numeric|min:0',
            'cost_price'     => 'nullable|numeric|min:0',
            'compare_price'  => 'nullable|numeric|min:0',
            'stock_quantity' => 'sometimes|integer|min:0',
            'is_active'      => 'sometimes|boolean',
            'is_featured'    => 'sometimes|boolean',
        ]);

        $product->update($validated);

        return response()->json(['success' => true, 'data' => $product, 'message' => 'Product updated']);
    }

    /** Delete any product */
    public function productDelete(Request $request, int $id)
    {
        $this->requireAdmin($request);
        Product::findOrFail($id)->delete();
        return response()->json(['success' => true, 'message' => 'Product deleted']);
    }
}
