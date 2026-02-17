<?php

namespace App\Http\Controllers\Api;

use App\Contracts\AIServiceInterface;
use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\Log;

class ChatController extends Controller
{
    protected AIServiceInterface $aiService;

    public function __construct(AIServiceInterface $aiService)
    {
        $this->aiService = $aiService;
    }

    /**
     * @OA\Post(
     *     path="/api/chat",
     *     tags={"AI Chat"},
     *     summary="Chat with the AI Assistant",
     *     description="Send a question to the RAG chatbot and get a context-aware response.",
     *     @OA\RequestBody(
     *         required=true,
     *         @OA\JsonContent(
     *             required={"question"},
     *             @OA\Property(property="question", type="string", example="What is your experience with Laravel?", description="User question"),
     *             @OA\Property(property="conversation_id", type="string", format="uuid", example="550e8400-e29b-41d4-a716-446655440000", description="Optional conversation ID for history"),
     *             @OA\Property(property="max_context_items", type="integer", example=5, description="Number of context items to retrieve")
     *         )
     *     ),
     *     @OA\Response(
     *         response=200,
     *         description="Successful response",
     *         @OA\JsonContent(
     *             @OA\Property(property="answer", type="string", example="I have 5 years of experience..."),
     *             @OA\Property(property="conversation_id", type="string", format="uuid"),
     *             @OA\Property(
     *                 property="sources",
     *                 type="array",
     *                 @OA\Items(
     *                     @OA\Property(property="id", type="integer"),
     *                     @OA\Property(property="content_preview", type="string"),
     *                     @OA\Property(property="similarity", type="number", format="float"),
     *                     @OA\Property(property="metadata", type="object")
     *                 )
     *             )
     *         )
     *     ),
     *     @OA\Response(
     *         response=422,
     *         description="Validation error"
     *     ),
     *     @OA\Response(
     *         response=500,
     *         description="Server error"
     *     )
     * )
     */
    public function chat(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'question' => 'required|string|max:1000',
            'conversation_id' => 'nullable|string|uuid',
            'max_context_items' => 'nullable|integer|min:1|max:10',
        ]);

        try {
            $response = $this->aiService->chat(
                $validated['question'],
                $validated['conversation_id'] ?? null,
                $validated['max_context_items'] ?? 5
            );

            return response()->json($response);

        } catch (\Exception $e) {
            Log::error('Chat proxy error', ['error' => $e->getMessage()]);

            return response()->json([
                'error' => 'Failed to process chat request',
                'details' => config('app.debug') ? $e->getMessage() : null
            ], 500);
        }
    }

    /**
     * @OA\Post(
     *     path="/api/chat/welcome",
     *     tags={"AI Chat"},
     *     summary="Get Smart Welcome Message",
     *     description="Generates a contextual welcome message for new or returning users.",
     *     @OA\RequestBody(
     *         required=false,
     *         @OA\JsonContent(
     *             @OA\Property(property="conversation_id", type="string", format="uuid", description="Optional conversation ID")
     *         )
     *     ),
     *     @OA\Response(
     *         response=200,
     *         description="Successful response",
     *         @OA\JsonContent(
     *             @OA\Property(property="message", type="string", example="Hola! Soy el asistente..."),
     *             @OA\Property(property="conversation_id", type="string", format="uuid")
     *         )
     *     )
     * )
     */
    public function welcome(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'conversation_id' => 'nullable|string|uuid',
        ]);

        try {
            $response = $this->aiService->getWelcomeMessage(
                $validated['conversation_id'] ?? null
            );

            return response()->json($response);

        } catch (\Exception $e) {
            Log::error('Welcome message error', ['error' => $e->getMessage()]);
            return response()->json([
                'message' => '¡Hola! Soy el asistente virtual de Reinaldo. ¿En qué puedo ayudarte hoy?',
                'conversation_id' => null
            ]);
        }
    }
}
