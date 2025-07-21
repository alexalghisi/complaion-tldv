import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
    HomeIcon,
    PlayIcon,
    BriefcaseIcon,
    Cog6ToothIcon
} from '@heroicons/react/24/outline';

const Navbar: React.FC = () => {
    const location = useLocation();

    const navigation = [
        { name: 'Dashboard', href: '/', icon: HomeIcon },
        { name: 'Jobs', href: '/jobs', icon: BriefcaseIcon },
        { name: 'Meetings', href: '/meetings', icon: PlayIcon },
    ];

    const isActive = (path: string) => {
        return location.pathname === path;
    };

    return (
        <nav className="bg-white shadow-sm border-b">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-16">
                    {/* Logo */}
                    <div className="flex items-center">
                        <Link to="/" className="flex items-center">
                            <div className="flex-shrink-0">
                                <div className="h-8 w-8 bg-indigo-600 rounded-lg flex items-center justify-center">
                                    <PlayIcon className="h-5 w-5 text-white" />
                                </div>
                            </div>
                            <div className="ml-3">
                                <span className="text-sm text-gray-500 ml-1">tl;dv</span>
                            </div>
                        </Link>
                    </div>

                    {/* Navigation Links */}
                    <div className="flex items-center space-x-8">
                        {navigation.map((item) => {
                            const Icon = item.icon;
                            return (
                                <Link
                                    key={item.name}
                                    to={item.href}
                                    className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                                        isActive(item.href)
                                            ? 'bg-indigo-100 text-indigo-700'
                                            : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                                    }`}
                                >
                                    <Icon className="h-4 w-4 mr-2" />
                                    {item.name}
                                </Link>
                            );
                        })}
                    </div>

                    {/* Right side - Settings */}
                    <div className="flex items-center">
                        <button
                            type="button"
                            className="p-2 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors"
                            title="Settings"
                        >
                            <Cog6ToothIcon className="h-5 w-5" />
                        </button>
                    </div>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;