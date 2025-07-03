/**
 * Tipi per API responses
 */

export interface ApiResponse<T = any> {
    data: T;
    message?: string;
    success: boolean;
}

export interface ApiError {
    message: string;
    details?: Record<string, any>;
    code?: string;
}

export interface PaginatedResponse<T> {
    page: number;
    pages: number;
    total: number;
    pageSize: number;
    results: T[];
}