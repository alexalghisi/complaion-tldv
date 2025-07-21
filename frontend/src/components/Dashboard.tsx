import React from 'react';
import { PlusIcon } from '@heroicons/react/24/outline';
import JobProgressCard from './JobProgressCard';
import CreateJobModal from './CreateJobModal';
import { Job } from '../types';

const jobs: Job[] = [
  {
    id: '1',
    name: 'Example Job',
    status: 'running',
    progress: { overall_percentage: 45 }
  },
  {
    id: '2',
    name: 'Finished Job',
    status: 'completed',
    progress: { overall_percentage: 100 }
  }
];

const Dashboard: React.FC = () => {
  const [isModalOpen, setModalOpen] = React.useState(false);

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Jobs Dashboard</h1>
        <button
          onClick={() => setModalOpen(true)}
          className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          Create Job
        </button>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {jobs.map((job: Job) => (
          <JobProgressCard key={job.id} job={job} />
        ))}
      </div>
      <CreateJobModal isOpen={isModalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
};

export default Dashboard;
