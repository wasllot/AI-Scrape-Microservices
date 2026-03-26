<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;

class ServiceController extends Controller
{
    public function index(Request $request)
    {
        // Devolvemos servicios hardcodeados de BASE para el Studio, 
        // o desde una base de datos si existe el modelo Service.
        $services = [
            ['id' => 1, 'name' => 'Audio', 'description' => 'Producción y diseño sonoro', 'isActive' => true],
            ['id' => 2, 'name' => 'Video', 'description' => 'Edición y postproducción', 'isActive' => true],
            ['id' => 3, 'name' => 'Diseño', 'description' => 'Diseño gráfico y UI/UX', 'isActive' => true],
        ];

        return response()->json([
            'success' => true,
            'data' => $services
        ]);
    }
}
