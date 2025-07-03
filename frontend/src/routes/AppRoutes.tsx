import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from '../components/Layout';
import Dashboard from '../pages/Dashboard';
import Meetings from '../pages/Meetings';
import Jobs from '../pages/Jobs';
import NotFound from '../pages/NotFound';

const AppRoutes: React.FC = () => {
    return (
        <Routes>
            <Route path="/" element={<Layout />}>
                <Route index element={<Dashboard />} />
                <Route path="meetings" element={<Meetings />} />
                <Route path="jobs" element={<Jobs />} />
                <Route path="*" element={<NotFound />} />
            </Route>
        </Routes>
    );
};

export default AppRoutes;