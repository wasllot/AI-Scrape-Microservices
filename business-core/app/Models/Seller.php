<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\Relations\HasOne;
use Illuminate\Support\Str;

class Seller extends Model
{
    protected $fillable = [
        'user_id',
        'store_name',
        'slug',
        'description',
        'logo',
        'banner',
        'rut',
        'bank_account',
        'bank_name',
        'whatsapp',
        'contact_email',
        'website',
        'address',
        'categories',
        'status',
        'rejection_reason',
        'commission_rate',
        'rating',
        'total_sales',
        'approved_at',
    ];

    protected function casts(): array
    {
        return [
            'approved_at' => 'datetime',
            'categories'  => 'array',
        ];
    }

    protected static function booted(): void
    {
        static::creating(function (Seller $seller) {
            if (empty($seller->slug)) {
                $seller->slug = Str::slug($seller->store_name);
            }
        });
    }

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function products(): HasMany
    {
        return $this->hasMany(Product::class);
    }

    public function orders(): HasMany
    {
        return $this->hasMany(Order::class);
    }

    public function activeProducts(): HasMany
    {
        return $this->hasMany(Product::class)->where('is_active', true);
    }

    public function isApproved(): bool
    {
        return $this->status === 'approved';
    }

    public function getTotalRevenueAttribute(): float
    {
        return $this->orders()
            ->where('payment_status', 'paid')
            ->sum('subtotal');
    }
}
