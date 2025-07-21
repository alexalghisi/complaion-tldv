import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { toast } from 'react-hot-toast';
import { Job, Meeting, ApiResponse, PaginatedResponse } from '../types';

// API base configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor for loading states
api.interceptors.request.use((config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
    (response) => response,
    (error) => {
        const message = error.response?.data?.message || error.message || 'An error occurred';
        console.error('API Error:', message);

        // Don't show toast for 404s or canceled requests
        if (error.response?.status !== 404 && !axios.isCancel(error)) {
            toast.error(message);
        }

        return Promise.reject(error);
    }
);

// Jobs API hooks
export const useJobs = (filters: Record<string, any> = {}) => {
    return useQuery({
        queryKey: ['jobs', filters],
        queryFn: async (): Promise<PaginatedResponse<Job>> => {
            const params = new URLSearchParams();
            Object.entries(filters).forEach(([key, value]) => {
                if (value !== undefined && value !== '') {
                    params.append(key, String(value));
                }
            });

            const response = await api.get(`/jobs?${params}`);
            return {
                page: response.data.page || 1,
                pages: Math.ceil((response.data.total || 0) / (response.data.pageSize || 50)),
                total: response.data.total || 0,
                pageSize: response.data.pageSize || 50,
                data: response.data.jobs || [],
                results: response.data.jobs || []
            };
        },
        refetchInterval: 5000, // Refetch every 5 seconds for real-time updates
        staleTime: 2000,
    });
};

export const useJob = (jobId: string) => {
    return useQuery({
        queryKey: ['job', jobId],
        queryFn: async (): Promise<Job> => {
            const response = await api.get(`/jobs/${jobId}`);
            return response.data.job;
        },
        enabled: !!jobId,
        refetchInterval: (data) => {
            // Refetch more frequently for active jobs
            const job = data as Job;
            if (job?.status === 'running' || job?.status === 'pending') {
                return 2000; // 2 seconds
            }
            return 10000; // 10 seconds for completed jobs
        },
    });
};

export const useCreateJob = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (jobData: {
            type: string;
            name: string;
            description?: string;
            config?: Record<string, any>;
            priority?: number;
        }) => {
            const response = await api.post('/jobs', jobData);
            return response.data;
        },
        onSuccess: (data) => {
            toast.success(`Job "${data.job.name}" created successfully!`);
            queryClient.invalidateQueries({ queryKey: ['jobs'] });
        },
        onError: (error: any) => {
            const message = error.response?.data?.message || 'Failed to create job';
            toast.error(message);
        },
    });
};

export const useRetryJob = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (jobId: string) => {
            const response = await api.post(`/jobs/${jobId}/retry`);
            return response.data;
        },
        onSuccess: (data, jobId) => {
            toast.success('Job retry initiated');
            queryClient.invalidateQueries({ queryKey: ['job', jobId] });
            queryClient.invalidateQueries({ queryKey: ['jobs'] });
        },
    });
};

// Meetings API hooks
export const useMeetings = (filters: Record<string, any> = {}) => {
    return useQuery({
        queryKey: ['meetings', filters],
        queryFn: async (): Promise<PaginatedResponse<Meeting>> => {
            const params = new URLSearchParams();
            Object.entries(filters).forEach(([key, value]) => {
                if (value !== undefined && value !== '') {
                    params.append(key, String(value));
                }
            });

            const response = await api.get(`/meetings?${params}`);
            return {
                page: response.data.page || 1,
                pages: response.data.pages || 1,
                total: response.data.total || 0,
                pageSize: response.data.pageSize || 50,
                data: response.data.meetings || [],
                results: response.data.meetings || []
            };
        },
        staleTime: 30000, // 30 seconds
    });
};

export const useMeeting = (meetingId: string, includeTranscript = false, includeHighlights = false) => {
    return useQuery({
        queryKey: ['meeting', meetingId, includeTranscript, includeHighlights],
        queryFn: async () => {
            const params = new URLSearchParams();
            if (includeTranscript) params.append('include_transcript', 'true');
            if (includeHighlights) params.append('include_highlights', 'true');

            const response = await api.get(`/meetings/${meetingId}?${params}`);
            return response.data;
        },
        enabled: !!meetingId,
        staleTime: 60000, // 1 minute
    });
};

export const useMeetingTranscript = (meetingId: string) => {
    return useQuery({
        queryKey: ['meeting', meetingId, 'transcript'],
        queryFn: async () => {
            const response = await api.get(`/meetings/${meetingId}/transcript`);
            return response.data.transcript;
        },
        enabled: !!meetingId,
        staleTime: 300000, // 5 minutes
    });
};

export const useMeetingHighlights = (meetingId: string) => {
    return useQuery({
        queryKey: ['meeting', meetingId, 'highlights'],
        queryFn: async () => {
            const response = await api.get(`/meetings/${meetingId}/highlights`);
            return response.data.highlights;
        },
        enabled: !!meetingId,
        staleTime: 300000, // 5 minutes
    });
};

// System API hooks
export const useSystemStats = () => {
    return useQuery({
        queryKey: ['system', 'stats'],
        queryFn: async () => {
            const response = await api.get('/stats');
            return response.data;
        },
        refetchInterval: 30000, // 30 seconds
        staleTime: 15000,
    });
};

export const useSystemHealth = () => {
    return useQuery({
        queryKey: ['system', 'health'],
        queryFn: async () => {
            const response = await api.get('/system/health');
            return response.data;
        },
        refetchInterval: 60000, // 1 minute
        retry: 2,
    });
};

export const useCeleryStatus = () => {
    return useQuery({
        queryKey: ['celery', 'status'],
        queryFn: async () => {
            const response = await api.get('/celery/status');
            return response.data;
        },
        refetchInterval: 10000, // 10 seconds
        staleTime: 5000,
    });
};

// Import meeting
export const useImportMeeting = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (importData: {
            name: string;
            url: string;
            happenedAt?: string;
            dryRun?: boolean;
        }) => {
            const response = await api.post('/import', importData);
            return response.data;
        },
        onSuccess: (data) => {
            toast.success('Meeting import started successfully!');
            queryClient.invalidateQueries({ queryKey: ['jobs'] });
        },
    });
};

// Bulk operations
export const useBulkJobAction = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (data: {
            action: 'retry' | 'cancel';
            job_ids: string[];
        }) => {
            const response = await api.post('/jobs/bulk-action', data);
            return response.data;
        },
        onSuccess: (data) => {
            const { action, results } = data.results;
            toast.success(`Bulk ${action} completed: ${results.successful}/${results.total_jobs} successful`);
            queryClient.invalidateQueries({ queryKey: ['jobs'] });
        },
    });
};

// Task status
export const useTaskStatus = (taskId: string) => {
    return useQuery({
        queryKey: ['task', taskId],
        queryFn: async () => {
            const response = await api.get(`/tasks/${taskId}`);
            return response.data;
        },
        enabled: !!taskId,
        refetchInterval: (data) => {
            // Stop refetching if task is complete
            if (data?.ready) {
                return false;
            }
            return 2000; // 2 seconds for running tasks
        },
        retry: 1,
    });
};

// Health check
export const useHealthCheck = () => {
    return useQuery({
        queryKey: ['health'],
        queryFn: async () => {
            const response = await api.get('/health');
            return response.data;
        },
        refetchInterval: 30000,
        staleTime: 15000,
    });
};

// Export the configured axios instance for direct use
export { api };