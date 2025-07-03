import React from 'react';
import { Routes, Route } from 'react-router-dom';

const AppRoutes: React.FC = () => {
    return (
        <Routes>
            <Route path="/" element={<div>Home page works!</div>} />
        </Routes>
    );
};

export default AppRoutes;
