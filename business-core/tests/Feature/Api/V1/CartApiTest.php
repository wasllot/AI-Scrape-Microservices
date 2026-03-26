<?php

namespace Tests\Feature\Api\V1;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class CartApiTest extends TestCase
{
    use RefreshDatabase;

    public function test_can_get_cart_when_authenticated()
    {
        $user = User::factory()->create();

        $response = $this->actingAs($user, 'api')->getJson('/api/v1/cart');

        $response->assertStatus(200)
                 ->assertJsonStructure([
                     'data',
                 ]);
    }

    public function test_cannot_access_cart_unauthenticated()
    {
        $response = $this->getJson('/api/v1/cart');

        $response->assertStatus(401);
    }

    public function test_can_clear_cart()
    {
        $user = User::factory()->create();

        $response = $this->actingAs($user, 'api')->deleteJson('/api/v1/cart');

        $response->assertStatus(200);
    }
}
