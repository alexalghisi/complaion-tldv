import { useState, useEffect, useCallback } from 'react';
import { initializeApp } from 'firebase/app';
import {
    getFirestore,
    doc,
    collection,
    onSnapshot,
    query,
    where,
    orderBy,
    limit as firestoreLimit,
    DocumentData,
    QueryConstraint,
    Unsubscribe
} from 'firebase/firestore';
import { Job } from '../types';

// Firebase configuration
const firebaseConfig = {
    apiKey: process.env.REACT_APP_FIREBASE_API_KEY,
    authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN,
    projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID,
    storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET,
    messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID,
    appId: process.env.REACT_APP_FIREBASE_APP_ID,
};

// Initialize Firebase
let app: any;
let db: any;

try {
    app = initializeApp(firebaseConfig);
    db = getFirestore(app);
} catch (error) {
    console.warn('Firebase not configured properly:', error);
}

// Hook for real-time job updates
export const useRealtimeJob = (jobId: string) => {
    const [job, setJob] = useState<Job | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!db || !jobId) {
            setLoading(false);
            return;
        }

        const jobRef = doc(db, 'jobs', jobId);

        const unsubscribe = onSnapshot(
            jobRef,
            (doc) => {
                if (doc.exists()) {
                    const data = doc.data();
                    setJob({
                        id: doc.id,
                        ...data,
                        createdAt: data.created_at?.toDate?.() || data.created_at,
                        startedAt: data.started_at?.toDate?.() || data.started_at,
                        completedAt: data.completed_at?.toDate?.() || data.completed_at,
                        updatedAt: data.updated_at?.toDate?.() || data.updated_at,
                    } as Job);
                    setError(null);
                } else {
                    setJob(null);
                    setError('Job not found');
                }
                setLoading(false);
            },
            (err) => {
                console.error('Error listening to job updates:', err);
                setError(err.message);
                setLoading(false);
            }
        );

        return () => unsubscribe();
    }, [jobId]);

    return { job, loading, error };
};

// Hook for real-time jobs list
export const useRealtimeJobs = (filters: {
    status?: string;
    limit?: number;
    orderBy?: string;
} = {}) => {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!db) {
            setLoading(false);
            return;
        }

        const constraints: QueryConstraint[] = [];

        // Add status filter
        if (filters.status) {
            constraints.push(where('status', '==', filters.status));
        }

        // Add ordering
        const orderField = filters.orderBy || 'created_at';
        constraints.push(orderBy(orderField, 'desc'));

        // Add limit
        if (filters.limit) {
            constraints.push(firestoreLimit(filters.limit));
        }

        const jobsQuery = query(collection(db, 'jobs'), ...constraints);

        const unsubscribe = onSnapshot(
            jobsQuery,
            (snapshot) => {
                const jobsData = snapshot.docs.map(doc => ({
                    id: doc.id,
                    ...doc.data(),
                    createdAt: doc.data().created_at?.toDate?.() || doc.data().created_at,
                    startedAt: doc.data().started_at?.toDate?.() || doc.data().started_at,
                    completedAt: doc.data().completed_at?.toDate?.() || doc.data().completed_at,
                    updatedAt: doc.data().updated_at?.toDate?.() || doc.data().updated_at,
                })) as Job[];

                setJobs(jobsData);
                setError(null);
                setLoading(false);
            },
            (err) => {
                console.error('Error listening to jobs updates:', err);
                setError(err.message);
                setLoading(false);
            }
        );

        return () => unsubscribe();
    }, [filters.status, filters.limit, filters.orderBy]);

    return { jobs, loading, error };
};

// Hook for real-time meetings
export const useRealtimeMeetings = (filters: {
    jobId?: string;
    limit?: number;
} = {}) => {
    const [meetings, setMeetings] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!db) {
            setLoading(false);
            return;
        }

        const constraints: QueryConstraint[] = [];

        // Add job filter
        if (filters.jobId) {
            constraints.push(where('job_id', '==', filters.jobId));
        }

        // Add ordering
        constraints.push(orderBy('happened_at', 'desc'));

        // Add limit
        if (filters.limit) {
            constraints.push(firestoreLimit(filters.limit));
        }

        const meetingsQuery = query(collection(db, 'meetings'), ...constraints);

        const unsubscribe = onSnapshot(
            meetingsQuery,
            (snapshot) => {
                const meetingsData = snapshot.docs.map(doc => ({
                    id: doc.id,
                    ...doc.data(),
                    happenedAt: doc.data().happened_at || doc.data().happenedAt,
                    createdAt: doc.data().created_at?.toDate?.() || doc.data().created_at,
                    updatedAt: doc.data().updated_at?.toDate?.() || doc.data().updated_at,
                }));

                setMeetings(meetingsData);
                setError(null);
                setLoading(false);
            },
            (err) => {
                console.error('Error listening to meetings updates:', err);
                setError(err.message);
                setLoading(false);
            }
        );

        return () => unsubscribe();
    }, [filters.jobId, filters.limit]);

    return { meetings, loading, error };
};

// Hook for job progress notifications
export const useJobNotifications = (onJobUpdate?: (job: Job) => void) => {
    const [notifications, setNotifications] = useState<Array<{
        id: string;
        type: 'success' | 'error' | 'info';
        message: string;
        timestamp: Date;
    }>>([]);

    useEffect(() => {
        if (!db) return;

        // Listen to job updates for notifications
        const jobsQuery = query(
            collection(db, 'jobs'),
            orderBy('updated_at', 'desc'),
            firestoreLimit(20)
        );

        let isInitialLoad = true;

        const unsubscribe = onSnapshot(jobsQuery, (snapshot) => {
            if (isInitialLoad) {
                isInitialLoad = false;
                return;
            }

            snapshot.docChanges().forEach((change) => {
                if (change.type === 'modified') {
                    const jobData = {
                        id: change.doc.id,
                        ...change.doc.data(),
                    } as Job;

                    // Call callback if provided
                    if (onJobUpdate) {
                        onJobUpdate(jobData);
                    }

                    // Generate notification based on status change
                    let notification: any = null;

                    if (jobData.status === 'completed') {
                        notification = {
                            id: `${jobData.id}-completed`,
                            type: 'success' as const,
                            message: `Job "${jobData.name}" completed successfully`,
                            timestamp: new Date(),
                        };
                    } else if (jobData.status === 'failed') {
                        notification = {
                            id: `${jobData.id}-failed`,
                            type: 'error' as const,
                            message: `Job "${jobData.name}" failed`,
                            timestamp: new Date(),
                        };
                    } else if (jobData.status === 'running') {
                        notification = {
                            id: `${jobData.id}-started`,
                            type: 'info' as const,
                            message: `Job "${jobData.name}" started processing`,
                            timestamp: new Date(),
                        };
                    }

                    if (notification) {
                        setNotifications(prev => [notification, ...prev.slice(0, 9)]); // Keep last 10
                    }
                }
            });
        });

        return () => unsubscribe();
    }, [onJobUpdate]);

    const clearNotifications = useCallback(() => {
        setNotifications([]);
    }, []);

    const removeNotification = useCallback((id: string) => {
        setNotifications(prev => prev.filter(n => n.id !== id));
    }, []);

    return {
        notifications,
        clearNotifications,
        removeNotification,
    };
};

// Hook for system status monitoring
export const useSystemStatus = () => {
    const [status, setStatus] = useState<{
        jobsCount: number;
        runningJobs: number;
        completedJobs: number;
        failedJobs: number;
        lastUpdate: Date;
    }>({
        jobsCount: 0,
        runningJobs: 0,
        completedJobs: 0,
        failedJobs: 0,
        lastUpdate: new Date(),
    });

    useEffect(() => {
        if (!db) return;

        const jobsQuery = query(collection(db, 'jobs'));

        const unsubscribe = onSnapshot(jobsQuery, (snapshot) => {
            let runningCount = 0;
            let completedCount = 0;
            let failedCount = 0;

            snapshot.docs.forEach(doc => {
                const status = doc.data().status;
                if (status === 'running' || status === 'pending') {
                    runningCount++;
                } else if (status === 'completed') {
                    completedCount++;
                } else if (status === 'failed') {
                    failedCount++;
                }
            });

            setStatus({
                jobsCount: snapshot.size,
                runningJobs: runningCount,
                completedJobs: completedCount,
                failedJobs: failedCount,
                lastUpdate: new Date(),
            });
        });

        return () => unsubscribe();
    }, []);

    return status;
};

// Connection status hook
export const useFirebaseConnection = () => {
    const [isConnected, setIsConnected] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!db) {
            setError('Firebase not configured');
            return;
        }

        // Test connection with a simple query
        const testQuery = query(collection(db, 'jobs'), firestoreLimit(1));

        const unsubscribe = onSnapshot(
            testQuery,
            () => {
                setIsConnected(true);
                setError(null);
            },
            (err) => {
                setIsConnected(false);
                setError(err.message);
            }
        );

        return () => unsubscribe();
    }, []);

    return { isConnected, error };
};

export { db };