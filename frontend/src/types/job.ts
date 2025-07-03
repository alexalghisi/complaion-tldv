/**
 * Tipi per Job
 */

export type JobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
export type JobType = 'sync_meetings' | 'download_transcript' | 'download_highlights' | 'download_video';

export interface Job {
    id: string;
    jobType: JobType;
    status: JobStatus;
    meetingId?: string;

    // Progress
    progressPercentage: number;
    currentStep?: string;
    totalSteps: number;

    // Timing
    createdAt: string;
    startedAt?: string;
    completedAt?: string;

    // Results
    result?: Record<string, any>;
    errorMessage?: string;
    errorDetails?: Record<string, any>;

    // Metadata
    metadata: Record<string, any>;

    // Computed
    durationSeconds?: number;
    isFinished: boolean;
}

export interface JobCreate {
    jobType: JobType;
    meetingId?: string;
    metadata?: Record<string, any>;
}