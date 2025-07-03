import React from 'react';
import { useToast } from '../../contexts/ToastContext';

const Toast = () => {
    const { toasts, removeToast } = useToast();

    if (toasts.length === 0) return null;

    const getToastStyles = (type) => {
        switch (type) {
            case 'success':
                return 'bg-green-500 text-white';
            case 'error':
                return 'bg-red-500 text-white';
            case 'warning':
                return 'bg-yellow-500 text-black';
            default:
                return 'bg-blue-500 text-white';
        }
    };

    const getToastIcon = (type) => {
        switch (type) {
            case 'success':
                return '✅';
            case 'error':
                return '❌';
            case 'warning':
                return '⚠️';
            default:
                return 'ℹ️';
        }
    };

    return (
        <div className="fixed top-4 right-4 z-50 space-y-2">
            {toasts.map((toast) => (
                <div
                    key={toast.id}
                    className={`px-4 py-3 rounded-md shadow-lg flex items-center space-x-3 min-w-80 ${getToastStyles(toast.type)} animate-slide-in`}
                >
                    <span className="text-lg">{getToastIcon(toast.type)}</span>
                    <span className="flex-1">{toast.message}</span>
                    <button
                        onClick={() => removeToast(toast.id)}
                        className="text-lg hover:opacity-75"
                    >
                        ×
                    </button>
                </div>
            ))}
        </div>
    );
};

export default Toast;