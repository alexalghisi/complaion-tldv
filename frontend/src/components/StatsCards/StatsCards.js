import React from 'react';

const StatsCards = ({ stats }) => {
    const cards = [
        {
            title: 'Processi Totali',
            value: stats.total,
            icon: '📊',
            color: 'bg-blue-500'
        },
        {
            title: 'Completati',
            value: stats.completed,
            icon: '✅',
            color: 'bg-green-500'
        },
        {
            title: 'In Corso',
            value: stats.running,
            icon: '⏳',
            color: 'bg-yellow-500'
        },
        {
            title: 'Falliti',
            value: stats.failed,
            icon: '❌',
            color: 'bg-red-500'
        }
    ];

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {cards.map((card, index) => (
                <div key={index} className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center">
                        <div className={`p-2 rounded-md ${card.color}`}>
                            <span className="text-white text-xl">{card.icon}</span>
                        </div>
                        <div className="ml-4">
                            <p className="text-sm font-medium text-gray-600">{card.title}</p>
                            <p className="text-2xl font-semibold text-gray-900">{card.value}</p>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
};

export default StatsCards;