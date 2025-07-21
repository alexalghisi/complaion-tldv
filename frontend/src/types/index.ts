// Frontend TypeScript type definitions

export interface Meeting {
    id: string;
    name: string;
    happenedAt: string;
    url?: string;
    organizer?: {
        name: string;
        email: string;
    };
    invitees?: Array<{
        name: string;
        email: string;
    }>;
    template?: string;
    extraProperties?: string;
    createdAt?: string;
    updatedAt?: string;
    jobId?: string;
}

export interface TranscriptSegment {
    speaker: string;
    text: string;
    startTime: number;
    endTime: number;
}

export interface Transcript {
    id: string;
    meetingId: string;
    data: TranscriptSegment[];
    createdAt?: string;
    updatedAt?: string;
}

export interface Highlight {
    text: string;
    startTime: number;
    source: 'manual' | 'auto';
    topic?: {
        title: string;
        summary: string;
    };
}

export interface Highlights {
    meetingId: string;
    data: Highlight[];
    createdAt?: string;
    updatedAt?: string;
}

export interface Job {
    id: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    startedAt: string;
    completedAt?: string;
    totalMeetings?: number;
    processedMeetings?: number;
    errors?: string[];
    createdAt?: string;
    updatedAt?: string;
    progress?: number;
    name?: string;
    description?: string;
}

export interface ApiResponse<T> {
    success: boolean;
    data?: T;
    message?: string;
    error?: string;
}

export interface PaginatedResponse<T> {
    page: number;
    pages: number;
    total: number;
    pageSize: number;
    results: T[];
}

export interface JobsResponse extends PaginatedResponse<Job> {}
export interface MeetingsResponse extends PaginatedResponse<Meeting> {}

// API Error types
export interface ApiError {
    message: string;
    statusCode?: number;
    details?: any;
}

// Component Props types
export interface TableColumn<T> {
    key: keyof T;
    title: string;
    render?: (value: any, record: T) => React.ReactNode;
    sortable?: boolean;
    width?: string;
}

export interface FilterOption {
    value: string | number;
    label: string;
}

export interface SearchFilters {
    query?: string;
    status?: string;
    dateFrom?: string;
    dateTo?: string;
    page?: number;
    limit?: number;
}

// Form types
export interface NewJobForm {
    name: string;
    description?: string;
    filters?: {
        dateFrom?: string;
        dateTo?: string;
        query?: string;
        onlyParticipated?: boolean;
        meetingType?: 'internal' | 'external';
    };
}

export interface ImportMeetingForm {
    name: string;
    url: string;
    happenedAt?: string;
    dryRun?: boolean;
}

// Firebase types
export interface FirebaseConfig {
    apiKey: string;
    authDomain: string;
    projectId: string;
    storageBucket: string;
    messagingSenderId: string;
    appId: string;
}

// Video player types
export interface VideoPlayerState {
    playing: boolean;
    duration: number;
    currentTime: number;
    volume: number;
    muted: boolean;
    fullscreen: boolean;
}

export interface VideoPlayerControls {
    play: () => void;
    pause: () => void;
    seek: (time: number) => void;
    setVolume: (volume: number) => void;
    toggleMute: () => void;
    toggleFullscreen: () => void;
}

// Toast notification types
export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
    id: string;
    type: ToastType;
    title: string;
    message?: string;
    duration?: number;
}

// Loading states
export interface LoadingState {
    isLoading: boolean;
    error?: string | null;
}

export interface AsyncState<T> extends LoadingState {
    data?: T;
}

// Query hooks types (React Query)
export interface UseJobsOptions extends SearchFilters {
    enabled?: boolean;
    refetchInterval?: number;
}

export interface UseMeetingsOptions extends SearchFilters {
    enabled?: boolean;
    refetchInterval?: number;
}

// WebSocket types for real-time updates
export interface WebSocketMessage {
    type: 'job_update' | 'meeting_update' | 'error';
    payload: any;
    timestamp: string;
}

export interface JobUpdatePayload {
    jobId: string;
    status: Job['status'];
    progress?: number;
    message?: string;
}

// Navigation types
export interface NavItem {
    name: string;
    href: string;
    icon: React.ComponentType<{ className?: string }>;
    current?: boolean;
}

// Statistics types
export interface DashboardStats {
    totalMeetings: number;
    activeJobs: number;
    completedJobs: number;
    failedJobs: number;
    storageUsed?: number;
    lastSyncAt?: string;
}

// Export utility types
export type ExportFormat = 'json' | 'csv' | 'xlsx';

export interface ExportOptions {
    format: ExportFormat;
    includeTranscripts?: boolean;
    includeHighlights?: boolean;
    dateRange?: {
        from: string;
        to: string;
    };
}