<?php

namespace Tests\Feature\Api\V1;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class OrderApiTest extends TestCase
{
    use RefreshDatabase;

    public function test_can_list_orders_authenticated()
    {
        $user = User::factory()->create();

        $response = $this->actingAs($user, 'api')->getJson('/api/v1/orders');

        $response->assertStatus(200)
                 ->assertJsonStructure([
                     'data'
                 ]);
    }

    public function test_cannot_access_orders_unauthenticated()
    {
        $response = $this->getJson('/api/v1/orders');

        $response->assertStatus(401);
    }

    public function test_can_track_order_not_found()
    {
        $user = User::factory()->create();

        $response = $this->actingAs($user, 'api')->getJson('/api/v1/orders/99999/track');

        $response->assertStatus(404);
    }
}
