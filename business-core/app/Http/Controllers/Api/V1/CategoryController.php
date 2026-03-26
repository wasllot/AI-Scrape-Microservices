<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use App\Models\Category;

class CategoryController extends Controller
{
    public function index(Request $request)
    {
        // Obtiene las categorías. Puede incluir subcategorías o filtrarse si se desea
        $categories = Category::whereNull('parent_id')->with('children')->get();
        
        return response()->json([
            'success' => true,
            'data' => $categories
        ]);
    }

    public function show($id)
    {
        $category = Category::with('children')->findOrFail($id);
        
        return response()->json([
            'success' => true,
            'data' => $category
        ]);
    }
}
