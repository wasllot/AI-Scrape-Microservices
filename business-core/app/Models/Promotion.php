<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Support\Str;

class Promotion extends Model
{
    protected $fillable = [
        'name', 'slug', 'description', 'type', 'value', 'min_purchase_amount', 'max_discount_amount',
        'starts_at', 'expires_at', 'usage_limit', 'used_count', 'per_user_limit', 'is_active', 'is_featured',
        'target', 'target_category_id', 'target_seller_id', 'code', 'terms_conditions'
    ];

    protected function casts(): array
    {
        return [
            'starts_at' => 'datetime',
            'expires_at' => 'datetime',
            'is_active' => 'boolean',
            'is_featured' => 'boolean',
        ];
    }

    protected static function booted(): void
    {
        static::creating(function (Promotion $promotion) {
            if (empty($promotion->slug)) {
                $promotion->slug = Str::slug($promotion->name);
            }
        });
    }

    public function scopeActive($query)
    {
        return $query->where('is_active', true)
            ->where('starts_at', '<=', now())
            ->where('expires_at', '>=', now());
    }

    public function productPromotions(): HasMany
    {
        return $this->hasMany(ProductPromotion::class);
    }

    public function isValid(): bool
    {
        return $this->is_active 
            && $this->starts_at <= now() 
            && $this->expires_at >= now()
            && (!$this->usage_limit || $this->used_count < $this->usage_limit);
    }

    public function calculateDiscount(float $amount): float
    {
        if (!$this->isValid()) {
            return 0;
        }

        if ($this->min_purchase_amount && $amount < $this->min_purchase_amount) {
            return 0;
        }

        $discount = 0;

        switch ($this->type) {
            case 'percentage':
                $discount = $amount * ($this->value / 100);
                break;
            case 'fixed':
                $discount = $this->value;
                break;
            case 'free_shipping':
                // Handle shipping discount separately
                break;
        }

        if ($this->max_discount_amount && $discount > $this->max_discount_amount) {
            $discount = $this->max_discount_amount;
        }

        return max(0, $discount);
    }
}

class ProductPromotion extends Model
{
    public $timestamps = false;
    protected $fillable = ['product_id', 'promotion_id'];

    public function promotion(): BelongsTo
    {
        return $this->belongsTo(Promotion::class);
    }

    public function product(): BelongsTo
    {
        return $this->belongsTo(Product::class);
    }
}

class PromotionUsage extends Model
{
    protected $fillable = ['promotion_id', 'user_id', 'order_id', 'discount_amount'];

    public function promotion(): BelongsTo
    {
        return $this->belongsTo(Promotion::class);
    }

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function order(): BelongsTo
    {
        return $this->belongsTo(Order::class);
    }
}
