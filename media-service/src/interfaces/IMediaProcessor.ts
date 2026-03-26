export interface ProcessResult {
    success: boolean;
    outputPath?: string;
    error?: string;
    metadata?: any;
}

export interface IMediaProcessor {
    /**
     * Processes a media file at the given input path and saves it to the output path.
     * Additional options can be provided.
     */
    process(inputPath: string, outputPath: string, options?: any): Promise<ProcessResult>;
}
