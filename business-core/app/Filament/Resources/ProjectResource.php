<?php

declare(strict_types=1);

namespace App\Filament\Resources;

use App\Filament\Resources\ProjectResource\Pages;
use App\Models\Project;
use App\Models\User;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Forms\Set;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;
use Illuminate\Support\Str;

class ProjectResource extends Resource
{
    protected static ?string $model = Project::class;

    protected static ?string $navigationIcon = 'heroicon-o-briefcase';

    protected static ?string $navigationGroup = 'Contenido';

    protected static ?int $navigationSort = 2;

    // ─── Form ─────────────────────────────────────────────────────────────────

    public static function form(Form $form): Form
    {
        return $form->schema([
            Forms\Components\Tabs::make('project_tabs')
                ->tabs([

                    // ── Tab 1: Información General ────────────────────────────
                    Forms\Components\Tabs\Tab::make('Información General')
                        ->icon('heroicon-o-information-circle')
                        ->schema([
                            Forms\Components\TextInput::make('title')
                                ->label('Nombre del proyecto')
                                ->required()
                                ->maxLength(255)
                                ->live(onBlur: true)
                                ->afterStateUpdated(fn(Set $set, ?string $state) => $set(
                                    'slug',
                                    Str::slug($state ?? '')
                                )),

                            Forms\Components\TextInput::make('slug')
                                ->label('Slug')
                                ->required()
                                ->unique(Project::class, 'slug', ignoreRecord: true)
                                ->maxLength(255),

                            Forms\Components\Textarea::make('description')
                                ->label('Descripción')
                                ->rows(4)
                                ->columnSpanFull(),

                            Forms\Components\Select::make('status')
                                ->label('Estado')
                                ->options(Project::statuses())
                                ->default(Project::STATUS_DRAFT)
                                ->required(),

                            Forms\Components\Select::make('user_id')
                                ->label('Cliente asignado')
                                ->relationship('client', 'name', fn($query) => $query->role('Client'))
                                ->searchable()
                                ->preload()
                                ->placeholder('Sin cliente asignado'),

                        ])->columns(2),

                    // ── Tab 2: Detalles Técnicos ──────────────────────────────
                    Forms\Components\Tabs\Tab::make('Detalles Técnicos')
                        ->icon('heroicon-o-code-bracket')
                        ->schema([
                            Forms\Components\FileUpload::make('cover_image')
                                ->label('Imagen de portada')
                                ->image()
                                ->directory('projects/covers')
                                ->columnSpanFull(),

                            Forms\Components\TextInput::make('tech_stack')
                                ->label('Stack tecnológico')
                                ->placeholder('Laravel, React, PostgreSQL...')
                                ->helperText('Separado por comas.')
                                ->columnSpanFull(),

                            Forms\Components\TextInput::make('repo_url')
                                ->label('Repositorio')
                                ->url()
                                ->prefixIcon('heroicon-o-code-bracket-square')
                                ->placeholder('https://github.com/...'),

                            Forms\Components\TextInput::make('live_url')
                                ->label('URL en producción')
                                ->url()
                                ->prefixIcon('heroicon-o-globe-alt')
                                ->placeholder('https://...'),

                            Forms\Components\DatePicker::make('started_at')
                                ->label('Inicio'),

                            Forms\Components\DatePicker::make('finished_at')
                                ->label('Finalización')
                                ->after('started_at'),
                        ])->columns(2),

                    // ── Tab 3: SEO ────────────────────────────────────────────
                    Forms\Components\Tabs\Tab::make('SEO')
                        ->icon('heroicon-o-magnifying-glass')
                        ->schema([
                            Forms\Components\Section::make('Meta Etiquetas')
                                ->description('Estos datos controlan cómo aparece el proyecto en buscadores y redes sociales.')
                                ->schema([
                                    Forms\Components\TextInput::make('seo_metadata.title')
                                        ->label('Meta Título')
                                        ->maxLength(60)
                                        ->helperText('Recomendado: 50–60 caracteres.')
                                        ->columnSpanFull(),

                                    Forms\Components\Textarea::make('seo_metadata.description')
                                        ->label('Meta Descripción')
                                        ->rows(3)
                                        ->maxLength(160)
                                        ->helperText('Recomendado: 120–160 caracteres.')
                                        ->columnSpanFull(),

                                    Forms\Components\TagsInput::make('seo_metadata.keywords')
                                        ->label('Palabras clave')
                                        ->helperText('Presiona Enter para añadir cada keyword.')
                                        ->columnSpanFull(),
                                ]),
                        ]),

                ])
                ->columnSpanFull(),
        ]);
    }

    // ─── Table ────────────────────────────────────────────────────────────────

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\ImageColumn::make('cover_image')
                    ->label('')
                    ->width(60)
                    ->height(40)
                    ->defaultImageUrl(asset('images/placeholder.png')),

                Tables\Columns\TextColumn::make('title')
                    ->label('Proyecto')
                    ->searchable()
                    ->sortable()
                    ->limit(50),

                Tables\Columns\TextColumn::make('client.name')
                    ->label('Cliente')
                    ->placeholder('—')
                    ->sortable(),

                Tables\Columns\BadgeColumn::make('status')
                    ->label('Estado')
                    ->colors([
                        'gray' => Project::STATUS_DRAFT,
                        'info' => Project::STATUS_ACTIVE,
                        'success' => Project::STATUS_COMPLETED,
                        'warning' => Project::STATUS_ARCHIVED,
                    ])
                    ->formatStateUsing(fn(string $state): string => Project::statuses()[$state] ?? $state),

                Tables\Columns\TextColumn::make('tech_stack')
                    ->label('Stack')
                    ->limit(40)
                    ->placeholder('—'),

                Tables\Columns\TextColumn::make('started_at')
                    ->label('Inicio')
                    ->date('d/m/Y')
                    ->sortable()
                    ->placeholder('—'),

                Tables\Columns\TextColumn::make('finished_at')
                    ->label('Fin')
                    ->date('d/m/Y')
                    ->sortable()
                    ->placeholder('—'),
            ])
            ->filters([
                Tables\Filters\SelectFilter::make('status')
                    ->label('Estado')
                    ->options(Project::statuses()),
            ])
            ->actions([
                Tables\Actions\EditAction::make(),
                Tables\Actions\DeleteAction::make(),
            ])
            ->bulkActions([
                Tables\Actions\BulkActionGroup::make([
                    Tables\Actions\DeleteBulkAction::make(),
                ]),
            ])
            ->defaultSort('updated_at', 'desc');
    }

    // ─── Pages ────────────────────────────────────────────────────────────────

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListProjects::route('/'),
            'create' => Pages\CreateProject::route('/create'),
            'edit' => Pages\EditProject::route('/{record}/edit'),
        ];
    }
}
