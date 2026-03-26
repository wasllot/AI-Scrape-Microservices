import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { mediaRouter } from './controllers/MediaController';
import './workers/mediaWorker'; // Initialize worker

dotenv.config();

const app = express();
const PORT = process.env.PORT || 8000;

app.use(cors());
app.use(express.json());

// Main media routes
app.use('/media', mediaRouter);

// Health check endpoint
app.get('/health', (req, res) => {
    res.status(200).json({ status: 'ok', service: 'media-service' });
});

app.listen(PORT, () => {
    console.log(`[Media Service] Server is running on port ${PORT}`);
});
