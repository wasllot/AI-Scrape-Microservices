<!DOCTYPE html>
<html>

<head>
    <title>New Contact Form Submission</title>
</head>

<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
        <h2 style="color: #007bff;">New Project Inquiry</h2>
        <p>You have received a new message from your portfolio contact form.</p>

        <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Name:</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{{ $data['name'] }}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Email:</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{{ $data['email'] }}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Project Type:</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{{ $data['project_type'] }}</td>
            </tr>
        </table>

        <div style="margin-top: 20px; background-color: #f9f9f9; padding: 15px; border-radius: 5px;">
            <strong>Message:</strong><br>
            <p style="white-space: pre-wrap;">{{ $data['message'] }}</p>
        </div>

        <p style="margin-top: 20px; font-size: 12px; color: #888;">
            Sent from {{ config('app.name') }} Contact Form.
        </p>
    </div>
</body>

</html>