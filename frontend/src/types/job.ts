export interface JobProgress {
  overall_percentage: number;
  current_step?: string;
  total_items?: number;
  processed_items?: number;
  total_steps?: number;
  completed_steps?: number;
}

export interface JobError {
  message: string;
}

export interface Job {
  id: string;
  name?: string;
  status?: 'running' | 'completed' | 'failed' | 'pending';
  type?: string;
  priority?: number;
  startedAt?: string;
  completedAt?: string;
  progress?: JobProgress;
  errors?: JobError[];
}
