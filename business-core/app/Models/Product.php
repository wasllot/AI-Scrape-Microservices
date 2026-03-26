<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Support\Str;

class Product extends Model
{
    protected $fillable = [
        'seller_id',
        'category_id',
        'name',
        'slug',
        'description',
        'short_description',
        'sku',
        'barcode',
        'price',
        'cost_price',
        'compare_price',
        'stock_quantity',
        'low_stock_threshold',
        'is_active',
        'is_featured',
        'allow_backorder',
        'meta_title',
        'meta_description',
        'views',
        'sales_count',
        'source',
        'ml_id',
        'ml_url',
        'ml_original_price',
    ];

    protected function casts(): array
    {
        return [
            'is_active' => 'boolean',
            'is_featured' => 'boolean',
            'allow_backorder' => 'boolean',
        ];
    }

    protected static function booted(): void
    {
        static::creating(function (Product $product) {
            if (empty($product->slug)) {
                $product->slug = Str::slug($product->name);
            }
        });
    }

    public function seller(): BelongsTo
    {
        return $this->belongsTo(Seller::class);
    }

    public function category(): BelongsTo
    {
        return $this->belongsTo(Category::class);
    }

    public function images(): HasMany
    {
        return $this->hasMany(ProductImage::class)->orderBy('sort_order');
    }

    public function primaryImage(): HasMany
    {
        return $this->hasMany(ProductImage::class)->where('is_primary', true);
    }

    public function variants(): HasMany
    {
        return $this->hasMany(ProductVariant::class);
    }

    public function promotions(): HasMany
    {
        return $this->hasMany(ProductPromotion::class);
    }

    public function scopeActive($query)
    {
        return $query->where('is_active', true);
    }

    public function scopeFeatured($query)
    {
        return $query->where('is_featured', true);
    }

    public function scopeOwn($query)
    {
        return $query->where('source', 'own');
    }

    public function scopeFromMl($query)
    {
        return $query->where('source', 'mercadolibre');
    }

    public function getDiscountPercentAttribute(): ?int
    {
        if ($this->compare_price && $this->compare_price > $this->price) {
            return round((($this->compare_price - $this->price) / $this->compare_price) * 100);
        }
        return null;
    }

    public function getFinalPriceAttribute(): float
    {
        $price = (float) $this->price;
        
        // Check for active promotions
        $promotion = $this->promotions()
            ->whereHas('promotion', function ($q) {
                $q->active();
            })
            ->first();
        
        if ($promotion) {
            $promo = $promotion->promotion;
            if ($promo->type === 'percentage') {
                $price = $price - ($price * $promo->value / 100);
            } elseif ($promo->type === 'fixed') {
                $price = $price - $promo->value;
            }
        }
        
        return max(0, $price);
    }

    public function isInStock(): bool
    {
        return $this->stock_quantity > 0 || $this->allow_backorder;
    }
}
