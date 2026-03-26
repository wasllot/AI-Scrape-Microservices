<?php

declare(strict_types=1);

namespace App\Filament\Resources;

use App\Filament\Resources\PostResource\Pages;
use App\Models\Post;
use App\Models\User;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Forms\Set;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;
use Illuminate\Support\Str;

class PostResource extends Resource
{
    protected static ?string $model = Post::class;

    protected static ?string $navigationIcon = 'heroicon-o-document-text';

    protected static ?string $navigationGroup = 'Contenido';

    protected static ?int $navigationSort = 1;

    // ─── Form ─────────────────────────────────────────────────────────────────

    public static function form(Form $form): Form
    {
        return $form->schema([
            Forms\Components\Tabs::make('post_tabs')
                ->tabs([

                    // ── Tab 1: Contenido ──────────────────────────────────────
                    Forms\Components\Tabs\Tab::make('Contenido')
                        ->icon('heroicon-o-pencil-square')
                        ->schema([
                            Forms\Components\TextInput::make('title')
                                ->label('Título')
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
                                ->unique(Post::class, 'slug', ignoreRecord: true)
                                ->maxLength(255),

                            Forms\Components\Textarea::make('excerpt')
                                ->label('Extracto')
                                ->rows(2)
                                ->maxLength(300)
                                ->columnSpanFull(),

                            Forms\Components\RichEditor::make('content')
                                ->label('Contenido')
                                ->required()
                                ->toolbarButtons([
                                    'attachFiles',
                                    'blockquote',
                                    'bold',
                                    'bulletList',
                                    'codeBlock',
                                    'h2',
                                    'h3',
                                    'italic',
                                    'link',
                                    'orderedList',
                                    'redo',
                                    'strike',
                                    'underline',
                                    'undo',
                                ])
                                ->columnSpanFull(),
                        ])->columns(2),

                    // ── Tab 2: Imagen y Publicación ───────────────────────────
                    Forms\Components\Tabs\Tab::make('Publicación')
                        ->icon('heroicon-o-calendar-days')
                        ->schema([
                            Forms\Components\FileUpload::make('cover_image')
                                ->label('Imagen de portada')
                                ->image()
                                ->directory('posts/covers')
                                ->columnSpanFull(),

                            Forms\Components\Select::make('status')
                                ->label('Estado')
                                ->options(Post::statuses())
                                ->default(Post::STATUS_DRAFT)
                                ->required()
                                ->live(),

                            Forms\Components\DateTimePicker::make('published_at')
                                ->label('Fecha de publicación')
                                ->visible(fn(Forms\Get $get) => $get('status') === Post::STATUS_PUBLISHED),

                            Forms\Components\Select::make('user_id')
                                ->label('Autor')
                                ->relationship('author', 'name')
                                ->searchable()
                                ->preload()
                                ->required(),
                        ])->columns(2),

                    // ── Tab 3: SEO ────────────────────────────────────────────
                    Forms\Components\Tabs\Tab::make('SEO')
                        ->icon('heroicon-o-magnifying-glass')
                        ->schema([
                            Forms\Components\Section::make('Meta Etiquetas')
                                ->description('Estos datos controlan cómo aparece el post en buscadores y redes sociales.')
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
                    ->label('Título')
                    ->searchable()
                    ->sortable()
                    ->limit(50),

                Tables\Columns\TextColumn::make('author.name')
                    ->label('Autor')
                    ->sortable(),

                Tables\Columns\BadgeColumn::make('status')
                    ->label('Estado')
                    ->colors([
                        'gray' => Post::STATUS_DRAFT,
                        'success' => Post::STATUS_PUBLISHED,
                        'warning' => Post::STATUS_ARCHIVED,
                    ])
                    ->formatStateUsing(fn(string $state): string => Post::statuses()[$state] ?? $state),

                Tables\Columns\TextColumn::make('published_at')
                    ->label('Publicado')
                    ->dateTime('d/m/Y H:i')
                    ->sortable()
                    ->placeholder('—'),

                Tables\Columns\TextColumn::make('updated_at')
                    ->label('Actualizado')
                    ->dateTime('d/m/Y')
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
            ])
            ->filters([
                Tables\Filters\SelectFilter::make('status')
                    ->label('Estado')
                    ->options(Post::statuses()),
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
            'index' => Pages\ListPosts::route('/'),
            'create' => Pages\CreatePost::route('/create'),
            'edit' => Pages\EditPost::route('/{record}/edit'),
        ];
    }
}
