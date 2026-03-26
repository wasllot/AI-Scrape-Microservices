<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Support\Str;

class Order extends Model
{
    protected $fillable = [
        'order_number', 'user_id', 'seller_id', 'shipping_address_id', 'billing_address_id',
        'status', 'subtotal', 'tax', 'shipping_cost', 'discount', 'total', 'currency',
        'payment_method', 'payment_status', 'payment_reference', 'shipping_method', 'tracking_number',
        'shipped_at', 'delivered_at', 'notes', 'customer_notes', 'paid_at', 'cancelled_at', 'cancellation_reason'
    ];

    protected function casts(): array
    {
        return [
            'shipped_at' => 'datetime',
            'delivered_at' => 'datetime',
            'paid_at' => 'datetime',
            'cancelled_at' => 'datetime',
        ];
    }

    protected static function booted(): void
    {
        static::creating(function (Order $order) {
            if (empty($order->order_number)) {
                $order->order_number = 'ORD-' . date('Ymd') . '-' . strtoupper(Str::random(6));
            }
        });
    }

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function seller(): BelongsTo
    {
        return $this->belongsTo(Seller::class);
    }

    public function shippingAddress(): BelongsTo
    {
        return $this->belongsTo(Address::class, 'shipping_address_id');
    }

    public function items(): HasMany
    {
        return $this->hasMany(OrderItem::class);
    }

    public function statusHistory(): HasMany
    {
        return $this->hasMany(OrderStatusHistory::class);
    }

    public function scopePending($query)
    {
        return $query->where('status', 'pending');
    }

    public function canCancel(): bool
    {
        return in_array($this->status, ['pending', 'confirmed']);
    }

    public function updateStatus(string $status, ?string $comment = null): void
    {
        $this->status = $status;
        $this->save();

        $this->statusHistory()->create([
            'status' => $status,
            'comment' => $comment,
        ]);

        if ($status === 'cancelled') {
            $this->cancelled_at = now();
            $this->save();
        }
    }
}

class OrderItem extends Model
{
    protected $fillable = [
        'order_id', 'product_id', 'product_variant_id', 'product_name', 'product_sku', 'product_image',
        'quantity', 'unit_price', 'tax_rate', 'tax_amount', 'discount', 'subtotal'
    ];

    public function order(): BelongsTo
    {
        return $this->belongsTo(Order::class);
    }

    public function product(): BelongsTo
    {
        return $this->belongsTo(Product::class);
    }
}

class OrderStatusHistory extends Model
{
    protected $fillable = ['order_id', 'status', 'comment', 'user_id'];

    public function order(): BelongsTo
    {
        return $this->belongsTo(Order::class);
    }

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }
}
