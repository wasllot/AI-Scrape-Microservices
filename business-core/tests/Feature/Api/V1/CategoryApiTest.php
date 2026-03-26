<?php

namespace Tests\Feature\Api\V1;

use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class CategoryApiTest extends TestCase
{
    use RefreshDatabase;

    public function test_can_list_categories()
    {
        $response = $this->getJson('/api/v1/categories');

        $response->assertStatus(200)
                 ->assertJsonStructure([
                     'data',
                 ]);
    }

    public function test_can_get_single_category_not_found()
    {
        $response = $this->getJson('/api/v1/categories/99999');

        $response->assertStatus(404);
    }

    public function test_can_get_search_filters()
    {
        $response = $this->getJson('/api/v1/search/filters');

        $response->assertStatus(200)
                 ->assertJsonStructure([
                     'data',
                 ]);
    }
}
