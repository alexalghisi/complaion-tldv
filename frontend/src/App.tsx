import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';
import AppRoutes from './routes/AppRoutes';

// Configurazione React Query
    const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            retry: 1,
            refetchOnWindowFocus: false,
            staleTime: 5 * 60 * 1000, // 5 minuti
        },
    },
});

function App() {
    return (
        <QueryClientProvider client={queryClient}>
            <Router>
                <div className="min-h-screen bg-gray-50">
                    <AppRoutes />
                    <Toaster
                        position="top-right"
                        toastOptions={{
                            duration: 4000,
                            style: {
                                background: '#363636',
                                color: '#fff',
                            },
                            success: {
                                iconTheme: {
                                    primary: '#4ade80',
                                    secondary: '#fff',
                                },
                            },
                            error: {
                                iconTheme: {
                                    primary: '#f87171',
                                    secondary: '#fff',
                                },
                            },
                        }}
                    />
                </div>
            </Router>
        </QueryClientProvider>
    );
}

export default App;