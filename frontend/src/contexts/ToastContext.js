import React, { createContext } from 'react';
import { useContext } from 'react';

export const ToastContext = createContext({});

export const ToastProvider = ({ children }) => (
    <ToastContext.Provider value={{}}>
        {children}
    </ToastContext.Provider>
);


export const useToast = () => useContext(ToastContext);
