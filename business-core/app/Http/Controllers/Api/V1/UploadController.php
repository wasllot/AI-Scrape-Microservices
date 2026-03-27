<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;

class UploadController extends Controller
{
    /**
     * @OA\Post(
     *     path="/api/v1/upload/image",
     *     tags={"Media"},
     *     summary="Subir Imagen Universal",
     *     description="Sube una imagen al bucket R2 y devuelve su URL pública para ser utilizada en creaciones de Productos, Tiendas o Categorías.",
     *     security={{"bearerAuth":{}}},
     *     @OA\RequestBody(
     *         required=true,
     *         @OA\MediaType(
     *             mediaType="multipart/form-data",
     *             @OA\Schema(
     *                 required={"image", "folder"},
     *                 @OA\Property(property="image", type="string", format="binary"),
     *                 @OA\Property(property="folder", type="string", enum={"products", "categories", "sellers", "avatars"})
     *             )
     *         )
     *     ),
     *     @OA\Response(response=200, description="Imagen subida exitosamente"),
     *     @OA\Response(response=401, description="No autorizado"),
     *     @OA\Response(response=422, description="Error de validación")
     * )
     */
    public function image(Request $request)
    {
        $request->validate([
            'image' => 'required|image|mimes:jpeg,png,jpg,webp,svg,gif|max:5120', // 5MB max
            'folder' => 'required|string|in:products,categories,sellers,avatars,misc',
        ]);

        $user = $request->user();
        if (!$user) {
            return response()->json(['success' => false, 'message' => 'Unauthorized'], 401);
        }

        try {
            $file = $request->file('image');
            $folder = $request->input('folder');
            $filename = uniqid() . '_' . time() . '.' . $file->getClientOriginalExtension();
            
            // Subir al disco R2
            $path = Storage::disk('r2')->putFileAs($folder, $file, $filename, 'public');

            // Formar la URL pública completa (tomando el R2_PUBLIC_URL desde el config que creamos)
            $publicUrl = config('filesystems.disks.r2.url') . '/' . $path;

            return response()->json([
                'success' => true,
                'message' => 'Image uploaded successfully to R2.',
                'data' => [
                    'path' => $path,
                    'url'  => $publicUrl
                ]
            ], 200);

        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to upload image.',
                'error' => $e->getMessage()
            ], 500);
        }
    }
}
