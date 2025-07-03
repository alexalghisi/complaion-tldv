import React from 'react';
import { useProcess } from '../../contexts/ProcessContext';
import { useToast } from '../../contexts/ToastContext';
import StatsCards from '../../components/StatsCards/StatsCards';
import RecentMeetings from '../../components/RecentMeetings/RecentMeetings';
import RecentProcesses from '../../components/RecentProcesses/RecentProcesses';

const Dashboard = () => {
    const { stats, startProcess, loading } = useProcess();
    const { success, error } = useToast();

    const handleStartSync = async () => {
        try {
            await startProcess();
            success('Processo di sincronizzazione avviato con successo!');
        } catch (err) {
            error('Errore nell\'avvio del processo: ' + err.message);
        }
    };

    return (
        <div className="space-y-6">
            {/* Header della dashboard */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
                    <p className="text-gray-600">
                        Panoramica dei processi e meeting tl;dv
                    </p>
                </div>

                <button
                    onClick={handleStartSync}
                    disabled={loading}
                    className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-4 py-2 rounded-md font-medium transition-colors flex items-center space-x-2"
                >
                    {loading ? (
                        <>
                            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                            <span>Avvio in corso...</span>
                        </>
                    ) : (
                        <>
                            <span>🚀</span>
                            <span>Avvia Sincronizzazione</span>
                        </>
                    )}
                </button>
            </div>

            {/* Cards statistiche */}
            <StatsCards stats={stats} />

            {/* Contenuto principale */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Meeting recenti */}
                <RecentMeetings />

                {/* Processi recenti */}
                <RecentProcesses />
            </div>
        </div>
    );
};

export default Dashboard;