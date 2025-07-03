import React, { createContext, useContext, useState } from 'react';

export const ProcessContext = createContext({
    completed: [],
    failed: [],
    running: [],
    addCompleted: () => {},
    addFailed: () => {},
    addRunning: () => {},
});

export const ProcessProvider = ({ children }) => {
    const [completed, setCompleted] = useState([]);
    const [failed, setFailed] = useState([]);
    const [running, setRunning] = useState([]);

    const addCompleted = (process) => setCompleted((prev) => [...prev, process]);
    const addFailed = (process) => setFailed((prev) => [...prev, process]);
    const addRunning = (process) => setRunning((prev) => [...prev, process]);

    return (
        <ProcessContext.Provider value={{ completed, failed, running, addCompleted, addFailed, addRunning }}>
            {children}
        </ProcessContext.Provider>
    );
};

export const useProcess = () => useContext(ProcessContext);
