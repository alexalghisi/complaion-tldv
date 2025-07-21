import React, { useEffect, useState } from 'react';
import { Transition } from '@headlessui/react';
import {
    CheckCircleIcon,
    ExclamationTriangleIcon,
    InformationCircleIcon,
    XMarkIcon
} from '@heroicons/react/24/outline';
import { useJobNotifications } from '../hooks/useFirebase';
import { toast } from 'react-hot-toast';

interface Notification {
    id: string;
    type: 'success' | 'error' | 'info' | 'warning';
    title: string;
    message: string;
    timestamp: Date;
    duration?: number;
}

const NotificationSystem: React.FC = () => {
    const [notifications, setNotifications] = useState<Notification[]>([]);

    // Use Firebase real-time notifications
    const { notifications: firebaseNotifications, removeNotification } = useJobNotifications((job) => {
        // Convert job updates to notifications
        let notification: Notification | null = null;

        if (job.status === 'completed') {
            notification = {
                id: `job-${job.id}-completed`,
                type: 'success',
                title: 'Job Completed',
                message: `"${job.name}" has completed successfully`,
                timestamp: new Date(),
                duration: 5000
            };
        } else if (job.status === 'failed') {
            notification = {
                id: `job-${job.id}-failed`,
                type: 'error',
                title: 'Job Failed',
                message: `"${job.name}" has failed`,
                timestamp: new Date(),
                duration: 8000
            };
        } else if (job.status === 'running') {
            notification = {
                id: `job-${job.id}-started`,
                type: 'info',
                title: 'Job Started',
                message: `"${job.name}" is now processing`,
                timestamp: new Date(),
                duration: 3000
            };
        }

        if (notification) {
            addNotification(notification);
        }
    });

    const addNotification = (notification: Notification) => {
        setNotifications(prev => [notification, ...prev.slice(0, 4)]); // Keep max 5 notifications

        // Auto-remove after duration
        if (notification.duration) {
            setTimeout(() => {
                removeNotificationById(notification.id);
            }, notification.duration);
        }
    };

    const removeNotificationById = (id: string) => {
        setNotifications(prev => prev.filter(n => n.id !== id));
    };

    const getIcon = (type: Notification['type']) => {
        switch (type) {
            case 'success':
                return <CheckCircleIcon className="h-6 w-6 text-green-400" />;
            case 'error':
                return <ExclamationTriangleIcon className="h-6 w-6 text-red-400" />;
            case 'warning':
                return <ExclamationTriangleIcon className="h-6 w-6 text-yellow-400" />;
            case 'info':
            default:
                return <InformationCircleIcon className="h-6 w-6 text-blue-400" />;
        }
    };

    const getColors = (type: Notification['type']) => {
        switch (type) {
            case 'success':
                return 'bg-white border border-green-200 shadow-lg';
            case 'error':
                return 'bg-white border border-red-200 shadow-lg';
            case 'warning':
                return 'bg-white border border-yellow-200 shadow-lg';
            case 'info':
            default:
                return 'bg-white border border-blue-200 shadow-lg';
        }
    };

    return (
        <div className="fixed top-4 right-4 z-50 space-y-4 w-96">
            {notifications.map((notification) => (
                <Transition
                    key={notification.id}
                    show={true}
                    enter="transform ease-out duration-300 transition"
                    enterFrom="translate-y-2 opacity-0 sm:translate-y-0 sm:translate-x-2"
                    enterTo="translate-y-0 opacity-100 sm:translate-x-0"
                    leave="transition ease-in duration-100"
                    leaveFrom="opacity-100"
                    leaveTo="opacity-0"
                >
                    <div className={`max-w-sm w-full rounded-lg pointer-events-auto ${getColors(notification.type)}`}>
                        <div className="p-4">
                            <div className="flex items-start">
                                <div className="flex-shrink-0">
                                    {getIcon(notification.type)}
                                </div>
                                <div className="ml-3 w-0 flex-1 pt-0.5">
                                    <p className="text-sm font-medium text-gray-900">
                                        {notification.title}
                                    </p>
                                    <p className="mt-1 text-sm text-gray-500">
                                        {notification.message}
                                    </p>
                                    <p className="mt-2 text-xs text-gray-400">
                                        {notification.timestamp.toLocaleTimeString()}
                                    </p>
                                </div>
                                <div className="ml-4 flex-shrink-0 flex">
                                    <button
                                        className="bg-white rounded-md inline-flex text-gray-400 hover:text-gray-500 focus:outline-none"
                                        onClick={() => removeNotificationById(notification.id)}
                                    >
                                        <span className="sr-only">Close</span>
                                        <XMarkIcon className="h-5 w-5" />
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </Transition>
            ))}
        </div>
    );
};

export default NotificationSystem;