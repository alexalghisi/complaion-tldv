import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import './App.css';

// Components
import Navbar from './components/Navbar';
import Dashboard from './components/Dashboard';
import JobsPage from './components/JobsPage';
import MeetingsPage from './components/MeetingsPage';
import MeetingDetail from './components/MeetingDetail';
import NotificationSystem from './components/NotificationSystem';

// Create React Query client
const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            retry: 1,
            refetchOnWindowFocus: false,
            staleTime: 5 * 60 * 1000, // 5 minutes
            cacheTime: 10 * 60 * 1000, // 10 minutes
        },
        mutations: {
            retry: 1,
        },
    },
});

const App: React.FC = () => {
    return (
        <QueryClientProvider client={queryClient}>
            <Router>
                <div className="min-h-screen bg-gray-50">
                    {/* Toast notifications */}
                    <Toaster
                        position="top-right"
                        toastOptions={{
                            duration: 4000,
                            style: {
                                background: '#363636',
                                color: '#fff',
                            },
                            success: {
                                duration: 3000,
                                iconTheme: {
                                    primary: '#4ade80',
                                    secondary: '#fff',
                                },
                            },
                            error: {
                                duration: 5000,
                                iconTheme: {
                                    primary: '#ef4444',
                                    secondary: '#fff',
                                },
                            },
                        }}
                    />

                    {/* Real-time notification system */}
                    <NotificationSystem />

                    {/* Navigation */}
                    <Navbar />

                    {/* Main Content */}
                    <main className="container mx-auto px-4 py-8">
                        <Routes>
                            {/* Dashboard - Overview */}
                            <Route path="/" element={<Dashboard />} />

                            {/* Jobs Management */}
                            <Route path="/jobs" element={<JobsPage />} />

                            {/* Meetings List */}
                            <Route path="/meetings" element={<MeetingsPage />} />

                            {/* Meeting Detail */}
                            <Route path="/meetings/:meetingId" element={<MeetingDetail />} />

                            {/* System Pages (placeholders for now) */}
                            <Route path="/system" element={<SystemPage />} />

                            {/* 404 Not Found */}
                            <Route path="*" element={<NotFound />} />
                        </Routes>
                    </main>
                </div>
            </Router>
        </QueryClientProvider>
    );
};

// System Page Component (placeholder)
const SystemPage: React.FC = () => {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">System Status</h1>
                <p className="mt-1 text-sm text-gray-500">
                    Monitor system health and performance
                </p>
            </div>

            <div className="bg-white shadow rounded-lg p-6">
                <div className="text-center py-12">
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                        System Monitoring
                    </h3>
                    <p className="text-gray-500 mb-4">
                        This page will be implemented in a future commit
                    </p>
                    <div className="text-sm text-gray-400">
                        Features coming soon:
                        <br />• Real-time service health monitoring
                        <br />• Performance metrics and analytics
                        <br />• System logs and debugging tools
                        <br />• Configuration management
                    </div>
                </div>
            </div>
        </div>
    );
};

// 404 Not Found Component
const NotFound: React.FC = () => {
    return (
        <div className="text-center py-12">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">404</h1>
            <p className="text-xl text-gray-600 mb-8">Pagina non trovata</p>
            <a
                href="/"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
                Torna alla Dashboard
            </a>
        </div>
    );
};

export default App;