<?php

declare(strict_types=1);

namespace App\Filament\Resources\ClientRequestResource\Pages;

use App\Filament\Resources\ClientRequestResource;
use Filament\Actions;
use Filament\Resources\Pages\ListRecords;

class ListClientRequests extends ListRecords
{
    protected static string $resource = ClientRequestResource::class;

    protected function getHeaderActions(): array
    {
        return [Actions\CreateAction::make()];
    }
}
