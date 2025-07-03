const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

class ApiService {
    async request(url, options = {}) {
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(`${API_BASE_URL}${url}`, config);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // Processi
    async getProcesses() {
        return this.request('/jobs');
    }

    async getProcess(id) {
        return this.request(`/jobs/${id}`);
    }

    async startDataSync() {
        return this.request('/jobs/start', {
            method: 'POST'
        });
    }

    // Meetings
    async getMeetings(page = 1, limit = 50) {
        return this.request(`/meetings?page=${page}&limit=${limit}`);
    }

    async getMeeting(id) {
        return this.request(`/meetings/${id}`);
    }

    // Health check
    async healthCheck() {
        return this.request('/health');
    }
}

export const apiService = new ApiService();