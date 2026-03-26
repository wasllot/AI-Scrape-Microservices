import { IMediaProcessor, ProcessResult } from '../interfaces/IMediaProcessor';
import ffmpeg from 'fluent-ffmpeg';

export class AudioProcessor implements IMediaProcessor {
    public async process(inputPath: string, outputPath: string, options: any = {}): Promise<ProcessResult> {
        return new Promise((resolve, reject) => {
            console.log(`[AudioProcessor] Processing audio from ${inputPath} to ${outputPath}`);

            let command = ffmpeg(inputPath);

            // Example option mapping (extendable)
            if (options.format) {
                command = command.format(options.format);
            }
            if (options.bitrate) {
                command = command.audioBitrate(options.bitrate);
            }

            command
                .on('end', () => {
                    console.log(`[AudioProcessor] Finished processing ${outputPath}`);
                    resolve({ success: true, outputPath });
                })
                .on('error', (err) => {
                    console.error(`[AudioProcessor] Error processing ${inputPath}:`, err);
                    reject(err);
                })
                .save(outputPath);
        });
    }
}
