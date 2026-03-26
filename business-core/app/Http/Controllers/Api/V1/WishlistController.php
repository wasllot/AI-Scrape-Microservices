<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;

class WishlistController extends Controller
{
    public function index(Request $request)
    {
        $user = $request->user();
        if (!$user) {
            return response()->json(['success' => false, 'message' => 'Unauthorized'], 401);
        }

        // Si existe relación users() -> wishlistedProducts() en User
        $wishlist = $user->wishlistedProducts()->with('images')->get();

        return response()->json([
            'success' => true,
            'data' => $wishlist
        ]);
    }

    public function store(Request $request)
    {
        $user = $request->user();
        if (!$user) {
            return response()->json(['success' => false, 'message' => 'Unauthorized'], 401);
        }

        $validated = $request->validate([
            'productId' => 'required|integer|exists:products,id'
        ]);

        $user->wishlistedProducts()->syncWithoutDetaching([$validated['productId']]);

        return response()->json([
            'success' => true,
            'message' => 'Product added to wishlist'
        ]);
    }

    public function destroy(Request $request, $productId)
    {
        $user = $request->user();
        if (!$user) {
            return response()->json(['success' => false, 'message' => 'Unauthorized'], 401);
        }

        $user->wishlistedProducts()->detach($productId);

        return response()->json([
            'success' => true,
            'message' => 'Product removed from wishlist'
        ]);
    }
}
