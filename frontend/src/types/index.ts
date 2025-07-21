export * from './job';

export interface Meeting {
  id: string;
  title: string;
  startedAt?: string;
  completedAt?: string;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
    data: T[];
    total: number;
    page: number;
    pageSize: number;
    pages?: number;
    results?: T[];
}