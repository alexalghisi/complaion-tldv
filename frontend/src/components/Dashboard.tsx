import React from 'react';
import { Link } from 'react-router-dom';
import {
    PlayIcon,
    BriefcaseIcon,
    DocumentTextIcon,
    ClockIcon,
    CheckCircleIcon,
    ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

// Mock data - will be replaced with real API calls
const mockStats = {
    totalMeetings: 142,
    activeJobs: 3,
    completedJobs: 28,
    failedJobs: 2
};

const mockRecentJobs = [
    {
        id: '1',
        name: 'Sales Team Weekly Sync',
        status: 'running',
        progress: 75,
        startedAt: '2024-01-15T10:30:00Z'
    },
    {
        id: '2',
        name: 'Product Strategy Meeting',
        status: 'completed',
        progress: 100,
        startedAt: '2024-01-15T09:00:00Z'
    },
    {
        id: '3',
        name: 'Customer Feedback Session',
        status: 'pending',
        progress: 0,
        startedAt: '2024-01-15T11:00:00Z'
    }
];

const Dashboard: React.FC = () => {
    return (
        <div className="space-y-6">
            {/* Page Header */}
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
                <p className="mt-1 text-sm text-gray-500">
                    Overview of your tl;dv meeting integration status
                </p>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
                <StatsCard
                    title="Total Meetings"
                    value={mockStats.totalMeetings}
                    icon={PlayIcon}
                    color="blue"
                    link="/meetings"
                />
                <StatsCard
                    title="Active Jobs"
                    value={mockStats.activeJobs}
                    icon={ClockIcon}
                    color="yellow"
                    link="/jobs?status=running"
                />
                <StatsCard
                    title="Completed Jobs"
                    value={mockStats.completedJobs}
                    icon={CheckCircleIcon}
                    color="green"
                    link="/jobs?status=completed"
                />
                <StatsCard
                    title="Failed Jobs"
                    value={mockStats.failedJobs}
                    icon={ExclamationTriangleIcon}
                    color="red"
                    link="/jobs?status=failed"
                />
            </div>

            {/* Recent Jobs */}
            <div className="bg-white shadow rounded-lg">
                <div className="px-4 py-5 sm:p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg leading-6 font-medium text-gray-900">
                            Recent Jobs
                        </h3>
                        <Link
                            to="/jobs"
                            className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
                        >
                            View all
                        </Link>
                    </div>

                    <div className="space-y-4">
                        {mockRecentJobs.map((job) => (
                            <JobItem key={job.id} job={job} />
                        ))}
                    </div>
                </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white shadow rounded-lg">
                <div className="px-4 py-5 sm:p-6">
                    <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                        Quick Actions
                    </h3>

                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                        <QuickActionCard
                            title="Start New Download"
                            description="Download meetings from tl;dv"
                            icon={BriefcaseIcon}
                            action={() => {
                                // TODO: Implement new job modal
                                alert('New job creation will be implemented in next commit');
                            }}
                        />
                        <QuickActionCard
                            title="View Documentation"
                            description="Learn how to use the integration"
                            icon={DocumentTextIcon}
                            action={() => {
                                window.open('https://doc.tldv.io', '_blank');
                            }}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
};

// Stats Card Component
interface StatsCardProps {
    title: string;
    value: number;
    icon: React.ComponentType<{ className?: string }>;
    color: 'blue' | 'green' | 'yellow' | 'red';
    link?: string;
}

const StatsCard: React.FC<StatsCardProps> = ({ title, value, icon: Icon, color, link }) => {
    const colorClasses = {
        blue: 'bg-blue-500',
        green: 'bg-green-500',
        yellow: 'bg-yellow-500',
        red: 'bg-red-500'
    };

    const content = (
        <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
                <div className="flex items-center">
                    <div className="flex-shrink-0">
                        <div className={`p-3 rounded-md ${colorClasses[color]}`}>
                            <Icon className="h-6 w-6 text-white" />
                        </div>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                        <dl>
                            <dt className="text-sm font-medium text-gray-500 truncate">
                                {title}
                            </dt>
                            <dd className="text-lg font-medium text-gray-900">
                                {value.toLocaleString()}
                            </dd>
                        </dl>
                    </div>
                </div>
            </div>
        </div>
    );

    if (link) {
        return <Link to={link}>{content}</Link>;
    }

    return content;
};

// Job Item Component
interface JobItemProps {
    job: {
        id: string;
        name: string;
        status: string;
        progress: number;
        startedAt: string;
    };
}

const JobItem: React.FC<JobItemProps> = ({ job }) => {
    const getStatusColor = (status: string) => {
        switch (status) {
            case 'running':
                return 'text-yellow-600 bg-yellow-100';
            case 'completed':
                return 'text-green-600 bg-green-100';
            case 'failed':
                return 'text-red-600 bg-red-100';
            default:
                return 'text-gray-600 bg-gray-100';
        }
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleString();
    };

    return (
        <div className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
            <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                    {job.name}
                </p>
                <p className="text-sm text-gray-500">
                    Started: {formatDate(job.startedAt)}
                </p>
            </div>

            <div className="flex items-center space-x-3">
                {job.status === 'running' && (
                    <div className="flex items-center">
                        <div className="w-24 bg-gray-200 rounded-full h-2">
                            <div
                                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                                style={{ width: `${job.progress}%` }}
                            />
                        </div>
                        <span className="ml-2 text-xs text-gray-500">{job.progress}%</span>
                    </div>
                )}

                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(job.status)}`}>
          {job.status}
        </span>
            </div>
        </div>
    );
};

// Quick Action Card Component
interface QuickActionCardProps {
    title: string;
    description: string;
    icon: React.ComponentType<{ className?: string }>;
    action: () => void;
}

const QuickActionCard: React.FC<QuickActionCardProps> = ({ title, description, icon: Icon, action }) => {
    return (
        <button
            onClick={action}
            className="relative p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-left"
        >
            <div className="flex items-start">
                <div className="flex-shrink-0">
                    <Icon className="h-6 w-6 text-indigo-600" />
                </div>
                <div className="ml-3">
                    <h4 className="text-sm font-medium text-gray-900">{title}</h4>
                    <p className="text-sm text-gray-500 mt-1">{description}</p>
                </div>
            </div>
        </button>
    );
};

export default Dashboard;