import { Queue } from 'bullmq';
import IORedis from 'ioredis';

// Connect to the shared redis instance defined in docker-compose
const connection = new IORedis({
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT || '6379', 10),
    maxRetriesPerRequest: null,
});

export const mediaQueueName = 'media-processing-queue';

// The Queue instance is our Producer
export const mediaQueue = new Queue(mediaQueueName, {
    connection: connection as any,
    defaultJobOptions: {
        attempts: 3,
        backoff: {
            type: 'exponential',
            delay: 1000,
        },
        removeOnComplete: true, // Keep it clean
        removeOnFail: false,    // Keep failed jobs for inspection
    },
});
