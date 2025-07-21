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

// Create React Query client
const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            retry: 1,
            refetchOnWindowFocus: false,
            staleTime: 5 * 60 * 1000, // 5 minutes
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

                            {/* 404 Not Found */}
                            <Route path="*" element={<NotFound />} />
                        </Routes>
                    </main>
                </div>
            </Router>
        </QueryClientProvider>
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