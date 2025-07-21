import { rest } from 'msw';
import { setupServer } from 'msw/node';
import { Job, Meeting } from '../types';

// Mock data
const mockJobs: Job[] = [
    {
        id: 'job-1',
        type: 'download_meetings',
        name: 'Test Download Job',
        status: 'completed',
        description: 'Test job description',
        priority: 2,
        createdAt: new Date('2024-01-15T10:00:00Z'),
        startedAt: new Date('2024-01-15T10:01:00Z'),
        completedAt: new Date('2024-01-15T10:15:00Z'),
        updatedAt: new Date('2024-01-15T10:15:00Z'),
        progress: {
            current_step: 'Completed',
            total_steps: 4,
            completed_steps: 4,
            processed_items: 25,
            total_items: 25,
        },
        result: {
            total_meetings: 25,
            processed_meetings: 25,
            failed_meetings: 0,
        },
        errors: [],
        retryCount: 0,
        maxRetries: 3,
    },
    {
        id: 'job-2',
        type: 'download_meetings',
        name: 'Running Job',
        status: 'running',
        description: 'Currently processing job',
        priority: 1,
        createdAt: new Date('2024-01-15T11:00:00Z'),
        startedAt: new Date('2024-01-15T11:01:00Z'),
        updatedAt: new Date('2024-01-15T11:05:00Z'),
        progress: {
            current_step: 'Processing meetings',
            total_steps: 4,
            completed_steps: 2,
            processed_items: 15,
            total_items: 30,
        },
        errors: [],
        retryCount: 0,
        maxRetries: 3,
    },
    {
        id: 'job-3',
        type: 'import_meeting',
        name: 'Failed Job',
        status: 'failed',
        description: 'This job failed',
        priority: 3,
        createdAt: new Date('2024-01-15T09:00:00Z'),
        startedAt: new Date('2024-01-15T09:01:00Z'),
        completedAt: new Date('2024-01-15T09:05:00Z'),
        updatedAt: new Date('2024-01-15T09:05:00Z'),
        errors: [
            {
                timestamp: new Date('2024-01-15T09:05:00Z'),
                error_code: 'API_ERROR',
                message: 'Failed to connect to tl;dv API',
                details: { status: 503 },
                retry_count: 0,
            },
        ],
        retryCount: 1,
        maxRetries: 3,
    },
];

const mockMeetings: Meeting[] = [
    {
        id: 'meeting-1',
        name: 'Weekly Team Sync',
        happenedAt: '2024-01-15T10:00:00Z',
        url: 'https://example.com/meeting1.mp4',
        organizer: {
            name: 'John Doe',
            email: 'john@example.com',
        },
        invitees: [
            { name: 'Jane Smith', email: 'jane@example.com' },
            { name: 'Bob Johnson', email: 'bob@example.com' },
        ],
        jobId: 'job-1',
        transcriptAvailable: true,
        highlightsAvailable: true,
        videoUrl: 'https://storage.example.com/video1.mp4',
        participantCount: 3,
    },
    {
        id: 'meeting-2',
        name: 'Product Strategy Meeting',
        happenedAt: '2024-01-14T14:00:00Z',
        url: 'https://example.com/meeting2.mp4',
        organizer: {
            name: 'Alice Brown',
            email: 'alice@example.com',
        },
        invitees: [
            { name: 'Charlie Wilson', email: 'charlie@example.com' },
        ],
        jobId: 'job-1',
        transcriptAvailable: false,
        highlightsAvailable: true,
        participantCount: 2,
    },
];

const mockStats = {
    jobs: {
        total_jobs: 3,
        pending_jobs: 0,
        running_jobs: 1,
        completed_jobs: 1,
        failed_jobs: 1,
    },
    meetings: {
        total_meetings: 2,
        meetings_with_transcript: 1,
        meetings_with_highlights: 2,
    },
};

// Request handlers
export const handlers = [
    // Health check
    rest.get('/api/health', (req, res, ctx) => {
        return res(
            ctx.status(200),
            ctx.json({
                status: 'healthy',
                timestamp: new Date().toISOString(),
                version: '1.0.0',
            })
        );
    }),

    // Jobs endpoints
    rest.get('/api/jobs', (req, res, ctx) => {
        const status = req.url.searchParams.get('status');
        const page = parseInt(req.url.searchParams.get('page') || '1');
        const limit = parseInt(req.url.searchParams.get('limit') || '50');

        let filteredJobs = mockJobs;
        if (status) {
            filteredJobs = mockJobs.filter(job => job.status === status);
        }

        const startIndex = (page - 1) * limit;
        const endIndex = startIndex + limit;
        const paginatedJobs = filteredJobs.slice(startIndex, endIndex);

        return res(
            ctx.status(200),
            ctx.json({
                jobs: paginatedJobs,
                total: filteredJobs.length,
                page,
                pageSize: limit,
                pages: Math.ceil(filteredJobs.length / limit),
            })
        );
    }),

    rest.get('/api/jobs/:jobId', (req, res, ctx) => {
        const { jobId } = req.params;
        const job = mockJobs.find(j => j.id === jobId);

        if (!job) {
            return res(ctx.status(404), ctx.json({ error: 'Job not found' }));
        }

        return res(ctx.status(200), ctx.json({ job }));
    }),

    rest.post('/api/jobs', (req, res, ctx) => {
        const newJob: Partial<Job> = {
            id: `job-${Date.now()}`,
            status: 'pending',
            createdAt: new Date(),
            updatedAt: new Date(),
            retryCount: 0,
            maxRetries: 3,
            errors: [],
            ...req.body,
        };

        return res(
            ctx.status(201),
            ctx.json({
                success: true,
                job_id: newJob.id,
                job: newJob,
                message: 'Job created successfully',
            })
        );
    }),

    rest.post('/api/jobs/:jobId/retry', (req, res, ctx) => {
        const { jobId } = req.params;
        const job = mockJobs.find(j => j.id === jobId);

        if (!job) {
            return res(ctx.status(404), ctx.json({ error: 'Job not found' }));
        }

        if (job.status !== 'failed') {
            return res(
                ctx.status(400),
                ctx.json({ error: 'Job cannot be retried' })
            );
        }

        // Simulate retry
        const updatedJob = {
            ...job,
            status: 'pending' as const,
            retryCount: job.retryCount + 1,
            updatedAt: new Date(),
        };

        return res(
            ctx.status(200),
            ctx.json({
                success: true,
                job: updatedJob,
                message: 'Job retry initiated',
            })
        );
    }),

    rest.post('/api/jobs/bulk-action', (req, res, ctx) => {
        const { action, job_ids } = req.body as { action: string; job_ids: string[] };

        const results = job_ids.map(jobId => {
            const job = mockJobs.find(j => j.id === jobId);
            return {
                job_id: jobId,
                success: !!job,
                error: job ? undefined : 'Job not found',
            };
        });

        return res(
            ctx.status(200),
            ctx.json({
                success: true,
                results: {
                    action,
                    total_jobs: job_ids.length,
                    successful: results.filter(r => r.success).length,
                    failed: results.filter(r => !r.success).length,
                    results,
                },
            })
        );
    }),

    // Meetings endpoints
    rest.get('/api/meetings', (req, res, ctx) => {
        const query = req.url.searchParams.get('query');
        const page = parseInt(req.url.searchParams.get('page') || '1');
        const limit = parseInt(req.url.searchParams.get('limit') || '50');

        let filteredMeetings = mockMeetings;
        if (query) {
            filteredMeetings = mockMeetings.filter(meeting =>
                meeting.name.toLowerCase().includes(query.toLowerCase())
            );
        }

        const startIndex = (page - 1) * limit;
        const endIndex = startIndex + limit;
        const paginatedMeetings = filteredMeetings.slice(startIndex, endIndex);

        return res(
            ctx.status(200),
            ctx.json({
                meetings: paginatedMeetings,
                total: filteredMeetings.length,
                page,
                pageSize: limit,
                pages: Math.ceil(filteredMeetings.length / limit),
            })
        );
    }),

    rest.get('/api/meetings/:meetingId', (req, res, ctx) => {
        const { meetingId } = req.params;
        const meeting = mockMeetings.find(m => m.id === meetingId);

        if (!meeting) {
            return res(ctx.status(404), ctx.json({ error: 'Meeting not found' }));
        }

        return res(
            ctx.status(200),
            ctx.json({
                meeting,
                source: 'local',
            })
        );
    }),

    rest.get('/api/meetings/:meetingId/transcript', (req, res, ctx) => {
        const { meetingId } = req.params;
        const meeting = mockMeetings.find(m => m.id === meetingId);

        if (!meeting || !meeting.transcriptAvailable) {
            return res(
                ctx.status(404),
                ctx.json({ error: 'Transcript not found' })
            );
        }

        return res(
            ctx.status(200),
            ctx.json({
                transcript: {
                    id: `transcript-${meetingId}`,
                    meeting_id: meetingId,
                    data: [
                        {
                            speaker: 'John Doe',
                            text: 'Welcome everyone to our weekly sync meeting.',
                            start_time: 0,
                            end_time: 3.5,
                        },
                        {
                            speaker: 'Jane Smith',
                            text: 'Thanks John. Let me start with the product updates.',
                            start_time: 4,
                            end_time: 7.2,
                        },
                    ],
                    total_duration: 1800,
                    word_count: 2500,
                },
            })
        );
    }),

    rest.get('/api/meetings/:meetingId/highlights', (req, res, ctx) => {
        const { meetingId } = req.params;
        const meeting = mockMeetings.find(m => m.id === meetingId);

        if (!meeting || !meeting.highlightsAvailable) {
            return res(
                ctx.status(404),
                ctx.json({ error: 'Highlights not found' })
            );
        }

        return res(
            ctx.status(200),
            ctx.json({
                highlights: {
                    meeting_id: meetingId,
                    data: [
                        {
                            text: 'We need to prioritize the mobile app development for Q2',
                            start_time: 450.5,
                            source: 'manual',
                            topic: {
                                title: 'Mobile Development',
                                summary: 'Discussion about mobile app priorities',
                            },
                        },
                    ],
                },
            })
        );
    }),

    // Stats endpoint
    rest.get('/api/stats', (req, res, ctx) => {
        return res(ctx.status(200), ctx.json(mockStats));
    }),

    // System endpoints
    rest.get('/api/system/health', (req, res, ctx) => {
        return res(
            ctx.status(200),
            ctx.json({
                timestamp: new Date().toISOString(),
                overall_status: 'healthy',
                services: {
                    tldv: { status: 'healthy', response_time_ms: 120 },
                    firebase: { status: 'healthy' },
                    celery: { status: 'healthy', active_workers: 2 },
                },
            })
        );
    }),

    rest.get('/api/celery/status', (req, res, ctx) => {
        return res(
            ctx.status(200),
            ctx.json({
                workers: {
                    active_count: 2,
                    worker_names: ['worker-1@localhost', 'worker-2@localhost'],
                    active_tasks: 1,
                },
                tasks: {
                    registered_count: 15,
                },
            })
        );
    }),

    // Import endpoint
    rest.post('/api/import', (req, res, ctx) => {
        return res(
            ctx.status(200),
            ctx.json({
                success: true,
                job_id: `import-job-${Date.now()}`,
                message: 'Import started successfully',
            })
        );
    }),
];

// Create server instance
export const server = setupServer(...handlers);