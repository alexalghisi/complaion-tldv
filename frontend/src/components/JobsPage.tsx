// frontend/src/components/JobsPage.tsx
import React from 'react';

const JobsPage: React.FC = () => {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Jobs</h1>
                <p className="mt-1 text-sm text-gray-500">
                    Manage your tl;dv download jobs
                </p>
            </div>

            <div className="bg-white shadow rounded-lg p-6">
                <div className="text-center py-12">
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                        Jobs Management
                    </h3>
                    <p className="text-gray-500 mb-4">
                        This page will be implemented in Commit 8
                    </p>
                    <div className="text-sm text-gray-400">
                        Features coming soon:
                        • Start new download jobs<br/>
                        • Monitor job progress<br/>
                        • View job history<br/>
                        • Retry failed jobs
                    </div>
                </div>
            </div>
        </div>
    );
};

export default JobsPage;
