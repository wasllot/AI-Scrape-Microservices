import { Router, Request, Response } from 'express';
import { mediaQueue } from '../queues/mediaQueue';

export const mediaRouter = Router();

mediaRouter.post('/process', async (req: Request, res: Response): Promise<void> => {
    try {
        const { type, inputPath, outputPath, options } = req.body;

        if (!type || !['audio', 'video', 'image'].includes(type)) {
            res.status(400).json({ error: 'Invalid or missing media type (audio, video, image).' });
            return;
        }

        if (!inputPath || !outputPath) {
            res.status(400).json({ error: 'Missing inputPath or outputPath.' });
            return;
        }

        // Add job to BullMQ
        const job = await mediaQueue.add(`process-${type}`, {
            type,
            inputPath,
            outputPath,
            options
        });

        res.status(202).json({
            message: 'Media processing job enqueued successfully.',
            jobId: job.id,
            type
        });
    } catch (error: any) {
        console.error('Error enqueuing media job:', error);
        res.status(500).json({ error: 'Internal server error while enqueuing job.' });
    }
});
