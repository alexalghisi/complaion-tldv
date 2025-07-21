// jest-dom adds custom jest matchers for asserting on DOM nodes.
import '@testing-library/jest-dom';
import { configure } from '@testing-library/react';
import { server } from './mocks/server';

// Configure testing library
configure({ testIdAttribute: 'data-testid' });

// Mock environment variables
process.env.REACT_APP_API_URL = 'http://localhost:5000/api';
process.env.REACT_APP_FIREBASE_PROJECT_ID = 'test-project';
process.env.REACT_APP_FIREBASE_API_KEY = 'test-api-key';
process.env.REACT_APP_FIREBASE_AUTH_DOMAIN = 'test-project.firebaseapp.com';
process.env.REACT_APP_FIREBASE_STORAGE_BUCKET = 'test-project.appspot.com';

// Mock Firebase
jest.mock('firebase/app', () => ({
    initializeApp: jest.fn(() => ({})),
}));

jest.mock('firebase/firestore', () => ({
    getFirestore: jest.fn(() => ({})),
    doc: jest.fn(),
    collection: jest.fn(),
    onSnapshot: jest.fn((query, callback) => {
        // Simulate real-time update
        setTimeout(() => {
            callback({
                exists: () => true,
                data: () => ({
                    id: 'test-job-1',
                    name: 'Test Job',
                    status: 'completed',
                    created_at: new Date(),
                }),
                id: 'test-job-1',
            });
        }, 100);

        // Return unsubscribe function
        return jest.fn();
    }),
    query: jest.fn(),
    where: jest.fn(),
    orderBy: jest.fn(),
    limit: jest.fn(),
}));

// Mock React Query
jest.mock('@tanstack/react-query', () => ({
    ...jest.requireActual('@tanstack/react-query'),
    useQuery: jest.fn(),
    useMutation: jest.fn(),
    useQueryClient: jest.fn(),
}));

// Mock React Router
jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: () => jest.fn(),
    useParams: () => ({ meetingId: 'test-meeting-1' }),
}));

// Mock Headless UI (for modals and dialogs)
jest.mock('@headlessui/react', () => ({
    Dialog: ({ children, open }: any) => open ? <div data-testid="dialog">{children}</div> : null,
        Transition: ({ children, show }: any) => show ? <div data-testid="transition">{children}</div> : null,
    Tab: {
    Group: ({ children }: any) => <div data-testid="tab-group">{children}</div>,
    List: ({ children }: any) => <div data-testid="tab-list">{children}</div>,
    Panels: ({ children }: any) => <div data-testid="tab-panels">{children}</div>,
    Panel: ({ children }: any) => <div data-testid="tab-panel">{children}</div>,
},
}));

// Mock toast notifications
jest.mock('react-hot-toast', () => ({
    toast: {
        success: jest.fn(),
        error: jest.fn(),
        loading: jest.fn(),
    },
    Toaster: () => <div data-testid="toaster" />,
}));

// Mock IntersectionObserver
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn(),
}));

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn(),
}));

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation(query => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: jest.fn(), // deprecated
        removeListener: jest.fn(), // deprecated
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
    })),
});

// Start MSW server before all tests
beforeAll(() => {
    server.listen({ onUnhandledRequest: 'error' });
});

// Reset handlers after each test
afterEach(() => {
    server.resetHandlers();
    jest.clearAllMocks();
});

// Clean up after all tests
afterAll(() => {
    server.close();
});