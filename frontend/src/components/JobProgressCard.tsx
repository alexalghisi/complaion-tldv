import React from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowPathIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import { Job } from '../types';

interface JobProgressCardProps {
  job: Job;
  detailed?: boolean;
}

const JobProgressCard: React.FC<JobProgressCardProps> = ({ job, detailed = false }) => {
  const currentJob = job;

  const getProgress = () => {
    if (currentJob.progress?.overall_percentage !== undefined) {
      return currentJob.progress.overall_percentage;
    }
    if (currentJob.status === 'completed') return 100;
    return 0;
  };

  return (
    <div className="border rounded-lg p-4">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2">
            <Link to={`/jobs/${currentJob.id}`} className="text-sm font-medium text-gray-900 hover:text-indigo-600 truncate">
              {currentJob.name}
            </Link>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Type: {currentJob.type || 'N/A'} • Priority: {currentJob.priority || 1}
          </p>
          <div className="mt-2">
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div
                className="bg-blue-600 h-2.5 rounded-full"
                style={{ width: `${getProgress()}%` }}
              ></div>
            </div>
            <p className="text-xs mt-1">{getProgress()}% complete</p>
          </div>
        </div>
        <div className="ml-2">
          {currentJob.status === 'completed' && <CheckCircleIcon className="h-5 w-5 text-green-500" />}
          {currentJob.status === 'failed' && <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />}
          {currentJob.status === 'running' && <ArrowPathIcon className="h-5 w-5 text-blue-500 animate-spin" />}
          {currentJob.status === 'pending' && <ClockIcon className="h-5 w-5 text-yellow-500" />}
        </div>
      </div>
    </div>
  );
};

export default JobProgressCard;
