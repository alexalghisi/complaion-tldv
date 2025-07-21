import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

// Custom render function that includes providers
const AllTheProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: {
                retry: false, // Disable retries in tests
                cacheTime: 0,
                staleTime: 0,
            },
            mutations: {
                retry: false,
            },
        },
    });

    return (
        <QueryClientProvider client={queryClient}>
            <BrowserRouter>
                <Toaster />
                {children}
            </BrowserRouter>
        </QueryClientProvider>
    );
};

const customRender = (
    ui: ReactElement,
    options?: Omit<RenderOptions, 'wrapper'>,
) => render(ui, { wrapper: AllTheProviders, ...options });

export * from '@testing-library/react';
export { customRender as render };

// Mock hooks for testing
export const mockUseQuery = (data: any, isLoading = false, error: any = null) => {
    return {
        data,
        isLoading,
        error,
        isError: !!error,
        isSuccess: !isLoading && !error,
        refetch: jest.fn(),
    };
};

export const mockUseMutation = (mutateAsync = jest.fn()) => {
    return {
        mutate: jest.fn(),
        mutateAsync,
        isLoading: false,
        isPending: false,
        isError: false,
        isSuccess: false,
        error: null,
        reset: jest.fn(),
    };
};

// Test data factories
export const createMockJob = (overrides = {}) => ({
    id: 'test-job-1',
    type: 'download_meetings',
    name: 'Test Job',
    status: 'completed',
    description: 'Test job description',
    priority: 1,
    createdAt: new Date('2024-01-15T10:00:00Z'),
    startedAt: new Date('2024-01-15T10:01:00Z'),
    completedAt: new Date('2024-01-15T10:05:00Z'),
    updatedAt: new Date('2024-01-15T10:05:00Z'),
    progress: {
        current_step: 'Completed',
        total_steps: 3,
        completed_steps: 3,
        processed_items: 10,
        total_items: 10,
    },
    errors: [],
    retryCount: 0,
    maxRetries: 3,
    ...overrides,
});

export const createMockMeeting = (overrides = {}) => ({
    id: 'test-meeting-1',
    name: 'Test Meeting',
    happenedAt: '2024-01-15T10:00:00Z',
    organizer: {
        name: 'John Doe',
        email: 'john@example.com',
    },
    invitees: [
        { name: 'Jane Smith', email: 'jane@example.com' },
    ],
    transcriptAvailable: true,
    highlightsAvailable: true,
    videoUrl: 'https://example.com/video.mp4',
    participantCount: 2,
    ...overrides,
});

export const createMockJobsResponse = (jobs = [createMockJob()]) => ({
    results: jobs,
    total: jobs.length,
    page: 1,
    pages: 1,
    pageSize: 50,
});

export const createMockMeetingsResponse = (meetings = [createMockMeeting()]) => ({
    results: meetings,
    total: meetings.length,
    page: 1,
    pages: 1,
    pageSize: 50,
});

// Wait for async operations
export const waitForLoadingToFinish = () =>
    new Promise(resolve => setTimeout(resolve, 0));

// User event utilities
export const clickButton = async (user: any, buttonText: string) => {
    const button = await user.findByRole('button', { name: buttonText });
    await user.click(button);
};

export const fillInput = async (user: any, labelText: string, value: string) => {
    const input = await user.findByLabelText(labelText);
    await user.clear(input);
    await user.type(input, value);
};

export const selectOption = async (user: any, labelText: string, value: string) => {
    const select = await user.findByLabelText(labelText);
    await user.selectOptions(select, value);
};

// Assert helpers
export const expectElementToBeVisible = (element: HTMLElement) => {
    expect(element).toBeInTheDocument();
    expect(element).toBeVisible();
};

export const expectButtonToBeEnabled = (button: HTMLElement) => {
    expect(button).toBeInTheDocument();
    expect(button).toBeEnabled();
};

export const expectButtonToBeDisabled = (button: HTMLElement) => {
    expect(button).toBeInTheDocument();
    expect(button).toBeDisabled();
};

// Mock Firebase hooks
export const mockFirebaseHooks = () => {
    jest.doMock('../hooks/useFirebase', () => ({
        useRealtimeJob: jest.fn(() => ({
            job: createMockJob(),
            loading: false,
            error: null,
        })),
        useRealtimeJobs: jest.fn(() => ({
            jobs: [createMockJob()],
            loading: false,
            error: null,
        })),
        useJobNotifications: jest.fn(() => ({
            notifications: [],
            removeNotification: jest.fn(),
        })),
        useFirebaseConnection: jest.fn(() => ({
            isConnected: true,
            error: null,
        })),
        useSystemStatus: jest.fn(() => ({
            jobsCount: 3,
            runningJobs: 1,
            completedJobs: 1,
            failedJobs: 1,
            lastUpdate: new Date(),
        })),
    }));
};

// Mock API hooks
export const mockApiHooks = () => {
    jest.doMock('../hooks/useApi', () => ({
        useJobs: jest.fn(() => mockUseQuery(createMockJobsResponse())),
        useJob: jest.fn(() => mockUseQuery(createMockJob())),
        useCreateJob: jest.fn(() => mockUseMutation()),
        useRetryJob: jest.fn(() => mockUseMutation()),
        useMeetings: jest.fn(() => mockUseQuery(createMockMeetingsResponse())),
        useMeeting: jest.fn(() => mockUseQuery({ meeting: createMockMeeting() })),
        useSystemStats: jest.fn(() => mockUseQuery({
            jobs: { total_jobs: 3, running_jobs: 1, completed_jobs: 1, failed_jobs: 1 },
            meetings: { total_meetings: 2 },
        })),
        useHealthCheck: jest.fn(() => mockUseQuery({ status: 'healthy' })),
        useBulkJobAction: jest.fn(() => mockUseMutation()),
        useImportMeeting: jest.fn(() => mockUseMutation()),
    }));
};

// Accessibility testing helper
export const checkAccessibility = async (container: HTMLElement) => {
    const { axe } = await import('@axe-core/react');
    const results = await axe(container);
    expect(results).toHaveNoViolations();
};