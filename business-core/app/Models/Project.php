<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Project extends Model
{
    use HasFactory;

    // ─── Status constants ─────────────────────────────────────────────────────

    const STATUS_DRAFT = 'draft';
    const STATUS_ACTIVE = 'active';
    const STATUS_COMPLETED = 'completed';
    const STATUS_ARCHIVED = 'archived';

    public static function statuses(): array
    {
        return [
            self::STATUS_DRAFT => 'Borrador',
            self::STATUS_ACTIVE => 'Activo',
            self::STATUS_COMPLETED => 'Completado',
            self::STATUS_ARCHIVED => 'Archivado',
        ];
    }

    // ─── Fillable ─────────────────────────────────────────────────────────────

    protected $fillable = [
        'user_id',
        'title',
        'slug',
        'description',
        'cover_image',
        'status',
        'tech_stack',
        'repo_url',
        'live_url',
        'started_at',
        'finished_at',
        'seo_metadata',
    ];

    // ─── Casts ────────────────────────────────────────────────────────────────

    protected function casts(): array
    {
        return [
            'seo_metadata' => 'array',
            'started_at' => 'date',
            'finished_at' => 'date',
        ];
    }

    // ─── Relationships ────────────────────────────────────────────────────────

    /** Cliente asignado al proyecto */
    public function client(): BelongsTo
    {
        return $this->belongsTo(User::class, 'user_id');
    }

    /** Tareas Kanban del proyecto (Paso 4) */
    public function tasks(): HasMany
    {
        return $this->hasMany(Task::class);
    }
}
