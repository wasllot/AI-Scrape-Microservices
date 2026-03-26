<?php

declare(strict_types=1);

namespace App\Filament\Resources;

use App\Filament\Resources\ClientRequestResource\Pages;
use App\Models\ClientRequest;
use App\Models\Project;
use App\Models\User;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;
use Illuminate\Support\Str;
use Filament\Notifications\Notification;

class ClientRequestResource extends Resource
{
    protected static ?string $model = ClientRequest::class;

    protected static ?string $navigationIcon = 'heroicon-o-inbox-arrow-down';

    protected static ?string $navigationGroup = 'Ventas y Clientes';

    protected static ?string $modelLabel = 'Solicitud';

    protected static ?string $pluralModelLabel = 'Solicitudes (Leads)';

    // ─── Form ─────────────────────────────────────────────────────────────────

    public static function form(Form $form): Form
    {
        return $form->schema([
            Forms\Components\Section::make('Datos del Lead')
                ->schema([
                    Forms\Components\TextInput::make('name')
                        ->label('Nombre')
                        ->required()
                        ->maxLength(255),

                    Forms\Components\TextInput::make('email')
                        ->label('Correo Electrónico')
                        ->email()
                        ->required()
                        ->maxLength(255),

                    Forms\Components\TextInput::make('budget')
                        ->label('Presupuesto')
                        ->maxLength(255),

                    Forms\Components\Select::make('status')
                        ->label('Estado')
                        ->options(ClientRequest::statuses())
                        ->default(ClientRequest::STATUS_PENDING)
                        ->required(),

                    Forms\Components\Textarea::make('description')
                        ->label('Descripción / Requerimiento')
                        ->required()
                        ->rows(5)
                        ->columnSpanFull(),
                ])->columns(2),
        ]);
    }

    // ─── Table ────────────────────────────────────────────────────────────────

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('name')
                    ->label('Nombre')
                    ->searchable()
                    ->sortable(),

                Tables\Columns\TextColumn::make('email')
                    ->label('Email')
                    ->searchable(),

                Tables\Columns\TextColumn::make('budget')
                    ->label('Presupuesto')
                    ->placeholder('—'),

                Tables\Columns\BadgeColumn::make('status')
                    ->label('Estado')
                    ->colors([
                        'warning' => ClientRequest::STATUS_PENDING,
                        'success' => ClientRequest::STATUS_APPROVED,
                        'danger' => ClientRequest::STATUS_REJECTED,
                    ])
                    ->formatStateUsing(fn(string $state): string => ClientRequest::statuses()[$state] ?? $state),

                Tables\Columns\TextColumn::make('created_at')
                    ->label('Fecha')
                    ->dateTime('d/m/Y H:i')
                    ->sortable(),
            ])
            ->filters([
                Tables\Filters\SelectFilter::make('status')
                    ->label('Estado')
                    ->options(ClientRequest::statuses()),
            ])
            ->actions([
                Tables\Actions\EditAction::make(),

                // ─── Custom Action: Aprobar y Crear Proyecto ──────────────────
                Tables\Actions\Action::make('approve_create_project')
                    ->label('Aprobar y Crear Proyecto')
                    ->icon('heroicon-o-check-circle')
                    ->color('success')
                    // Ocultar la acción si ya está aprobado
                    ->visible(fn(ClientRequest $record): bool => $record->isPending())
                    // Require confirmation and additional data (User assignment)
                    ->requiresConfirmation()
                    ->modalHeading('Aprobar Solicitud y Crear Proyecto')
                    ->modalDescription('Esto creará un nuevo proyecto usando los datos de la solicitud. Selecciona el cliente a asignar (debes crearlo previamente en Usuarios si no existe).')
                    ->form([
                        Forms\Components\Select::make('user_id')
                            ->label('Asignar Cliente')
                            ->options(User::role('Client')->pluck('name', 'id'))
                            ->searchable()
                            ->required()
                            ->helperText('Solo usuarios con rol "Client" aparecen aquí.'),
                    ])
                    ->action(function (ClientRequest $record, array $data): void {
                        // 1. Create the project
                        $project = Project::create([
                            'user_id' => $data['user_id'],
                            'title' => 'Proyecto: ' . $record->name,
                            'slug' => Str::slug('Proyecto ' . $record->name . ' ' . uniqid()),
                            'description' => "Presupuesto: {$record->budget}\n\nRequerimiento:\n{$record->description}",
                            'status' => Project::STATUS_DRAFT,
                        ]);

                        // 2. Update request status
                        $record->update(['status' => ClientRequest::STATUS_APPROVED]);

                        // 3. Notify
                        Notification::make()
                            ->title('Proyecto Creado Exitosamente')
                            ->body("El proyecto '{$project->title}' ha sido generado.")
                            ->success()
                            ->send();
                    }),
            ])
            ->bulkActions([
                Tables\Actions\BulkActionGroup::make([
                    Tables\Actions\DeleteBulkAction::make(),
                ]),
            ])
            ->defaultSort('created_at', 'desc');
    }

    // ─── Pages ────────────────────────────────────────────────────────────────

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListClientRequests::route('/'),
            'create' => Pages\CreateClientRequest::route('/create'),
            'edit' => Pages\EditClientRequest::route('/{record}/edit'),
        ];
    }
}
