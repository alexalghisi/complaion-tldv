import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useProcess } from '../../contexts/ProcessContext';
import Toast from '../Toast/Toast';

const Layout = ({ children }) => {
    const location = useLocation();
    const { stats } = useProcess();

    const navigation = [
        { name: 'Dashboard', href: '/', icon: '📊' },
        { name: 'Meetings', href: '/meetings', icon: '📹' },
        { name: 'Processes', href: '/processes', icon: '⚙️' }
    ];

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white shadow-sm border-b">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center h-16">
                        <div className="flex items-center">
                            <h1 className="text-xl font-bold text-gray-900">
                                🎬 tl;dv Integration Dashboard
                            </h1>
                        </div>

                        {/* Stats nella header */}
                        <div className="hidden md:flex items-center space-x-4">
                            <div className="flex items-center space-x-2 text-sm text-gray-600">
                                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                                <span>Completati: {stats.completed}</span>
                            </div>
                            <div className="flex items-center space-x-2 text-sm text-gray-600">
                                <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
                                <span>In corso: {stats.running}</span>
                            </div>
                            <div className="flex items-center space-x-2 text-sm text-gray-600">
                                <span className="w-2 h-2 bg-red-500 rounded-full"></span>
                                <span>Falliti: {stats.failed}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            <div className="flex">
                {/* Sidebar */}
                <nav className="w-64 bg-white shadow-sm h-screen">
                    <div className="p-4">
                        <div className="space-y-2">
                            {navigation.map((item) => {
                                const isActive = location.pathname === item.href;
                                return (
                                    <Link
                                        key={item.name}
                                        to={item.href}
                                        className={`flex items-center px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                                            isActive
                                                ? 'bg-blue-100 text-blue-700'
                                                : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                                        }`}
                                    >
                                        <span className="mr-3">{item.icon}</span>
                                        {item.name}
                                    </Link>
                                );
                            })}
                        </div>
                    </div>
                </nav>

                {/* Main content */}
                <main className="flex-1 p-6">
                    {children}
                </main>
            </div>

            {/* Toast notifications */}
            <Toast />
        </div>
    );
};

export default Layout;