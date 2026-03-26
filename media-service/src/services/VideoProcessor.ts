import { IMediaProcessor, ProcessResult } from '../interfaces/IMediaProcessor';
import ffmpeg from 'fluent-ffmpeg';

export class VideoProcessor implements IMediaProcessor {
    public async process(inputPath: string, outputPath: string, options: any = {}): Promise<ProcessResult> {
        return new Promise((resolve, reject) => {
            console.log(`[VideoProcessor] Processing video from ${inputPath} to ${outputPath}`);

            let command = ffmpeg(inputPath);

            // Example option mapping
            if (options.resolution) {
                command = command.size(options.resolution); // e.g. '1280x720' or '50%'
            }
            if (options.fps) {
                command = command.fps(options.fps);
            }
            if (options.videoBitrate) {
                command = command.videoBitrate(options.videoBitrate);
            }

            command
                .on('end', () => {
                    console.log(`[VideoProcessor] Finished processing ${outputPath}`);
                    resolve({ success: true, outputPath });
                })
                .on('error', (err) => {
                    console.error(`[VideoProcessor] Error processing ${inputPath}:`, err);
                    reject(err);
                })
                .save(outputPath);
        });
    }
}
