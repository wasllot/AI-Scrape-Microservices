<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Mail\ContactFormMail;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Mail;
use Illuminate\Support\Facades\Validator;


use App\Models\Contact;

class ContactController extends Controller
{
    /**
     * Handle incoming contact form submission.
     *
     * @param  \Illuminate\Http\Request  $request
     * @return \Illuminate\Http\JsonResponse
     */
    public function submit(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'name' => 'required|string|max:255',
            'email' => 'required|email|max:255',
            'project_type' => 'required|string|max:100',
            'message' => 'required|string|max:5000',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'errors' => $validator->errors()
            ], 422);
        }

        $data = $validator->validated();

        try {
            // Save to database
            $contact = Contact::create($data);

            // Send email to the site owner (configured in .env)
            $recipient = config('mail.from.address');

            if ($recipient) {
                try {
                    Mail::to($recipient)->send(new ContactFormMail($data));
                } catch (\Exception $e) {
                    // Log email error but don't fail the request if contact is saved
                    // Log::error('Failed to send contact email: ' . $e->getMessage());
                }
            }

            return response()->json([
                'success' => true,
                'message' => 'Message sent successfully!',
                'data' => $contact
            ], 200);

        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to save message. Please try again later.',
                'error' => config('app.debug') ? $e->getMessage() : null
            ], 500);
        }
    }

    /**
     * List all contact form submissions.
     *
     * @return \Illuminate\Http\JsonResponse
     */
    public function index()
    {
        $contacts = Contact::orderBy('created_at', 'desc')->paginate(10);

        return response()->json([
            'success' => true,
            'data' => $contacts
        ], 200);
    }
}
