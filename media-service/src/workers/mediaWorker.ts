import { Worker, Job } from 'bullmq';
import IORedis from 'ioredis';
import { mediaQueueName } from '../queues/mediaQueue';

import { AudioProcessor } from '../services/AudioProcessor';
import { VideoProcessor } from '../services/VideoProcessor';
import { ImageProcessor } from '../services/ImageProcessor';

const connection = new IORedis({
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT || '6379', 10),
    maxRetriesPerRequest: null,
});

const audioProcessor = new AudioProcessor();
const videoProcessor = new VideoProcessor();
const imageProcessor = new ImageProcessor();

export const mediaWorker = new Worker(
    mediaQueueName,
    async (job: Job) => {
        const { type, inputPath, outputPath, options } = job.data;
        console.log(`[MediaWorker] Processing job ${job.id} of type ${type}`);

        try {
            let result;
            switch (type) {
                case 'audio':
                    result = await audioProcessor.process(inputPath, outputPath, options);
                    break;
                case 'video':
                    result = await videoProcessor.process(inputPath, outputPath, options);
                    break;
                case 'image':
                    result = await imageProcessor.process(inputPath, outputPath, options);
                    break;
                default:
                    throw new Error(`Unsupported media type: ${type}`);
            }
            console.log(`[MediaWorker] Job ${job.id} completed successfully`);
            return result;
        } catch (error: any) {
            console.error(`[MediaWorker] Job ${job.id} failed:`, error.message);
            throw error;
        }
    },
    { connection: connection as any }
);

mediaWorker.on('completed', (job: Job, result: any) => {
    console.log(`Job ${job.id} has completed! Result:`, result);
});

mediaWorker.on('failed', (job: Job | undefined, err: Error) => {
    console.log(`Job ${job?.id} has failed with ${err.message}`);
});
