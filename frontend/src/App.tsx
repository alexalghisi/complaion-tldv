import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ProcessProvider } from './contexts/ProcessContext';
import { ToastProvider } from './contexts/ToastContext';
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard/Dashboard';
import Meetings from './pages/Meetings/Meetings';
import ProcessMonitor from './pages/ProcessMonitor/ProcessMonitor';
import './App.css';

function App() {
    return (
        <ToastProvider>
            <ProcessProvider>
                <Router>
                    <div className="App">
                        <Layout>
                            <Routes>
                                <Route path="/" element={<Dashboard />} />
                                <Route path="/meetings" element={<Meetings />} />
                                <Route path="/processes" element={<ProcessMonitor />} />
                            </Routes>
                        </Layout>
                    </div>
                </Router>
            </ProcessProvider>
        </ToastProvider>
    );
}

export default App;