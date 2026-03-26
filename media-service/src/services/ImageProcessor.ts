import { IMediaProcessor, ProcessResult } from '../interfaces/IMediaProcessor';
import sharp from 'sharp';

export class ImageProcessor implements IMediaProcessor {
    public async process(inputPath: string, outputPath: string, options: any = {}): Promise<ProcessResult> {
        try {
            console.log(`[ImageProcessor] Processing image from ${inputPath} to ${outputPath}`);

            let transform = sharp(inputPath);

            if (options.resize) {
                // e.g. { width: 800, height: 600 }
                transform = transform.resize(options.resize.width, options.resize.height, options.resize.options);
            }

            if (options.format) {
                // e.g. 'jpeg', 'png', 'webp'
                transform = transform.toFormat(options.format, options.formatOptions);
            }

            if (options.quality) {
                transform = transform.jpeg({ quality: options.quality }); // General quality fallback
            }

            await transform.toFile(outputPath);
            console.log(`[ImageProcessor] Finished processing ${outputPath}`);

            return { success: true, outputPath };
        } catch (error: any) {
            console.error(`[ImageProcessor] Error processing ${inputPath}:`, error);
            throw error;
        }
    }
}
