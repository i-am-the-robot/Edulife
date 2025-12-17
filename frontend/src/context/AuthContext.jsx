// Authentication Context
import { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/authService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check for existing token on mount
        const storedToken = sessionStorage.getItem('token');
        const storedUser = sessionStorage.getItem('user');

        if (storedToken && storedUser) {
            setToken(storedToken);
            setUser(JSON.parse(storedUser));
        }

        // Clean up old localStorage data (migration from localStorage to sessionStorage)
        if (localStorage.getItem('token') || localStorage.getItem('user')) {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
        }

        setLoading(false);
    }, []);

    const login = async (credentials, userType) => {
        try {
            let response;

            if (userType === 'student') {
                response = await authService.loginStudent(credentials.studentId, credentials.pin);
            } else if (userType === 'teacher') {
                response = await authService.loginTeacher(credentials.email, credentials.password);
            } else if (userType === 'admin') {
                response = await authService.loginAdmin(credentials.email, credentials.password);
            }

            const { access_token, ...userData } = response;

            console.log('Login successful:', { userType, userData });

            sessionStorage.setItem('token', access_token);
            sessionStorage.setItem('user', JSON.stringify({ ...userData, role: userType }));

            setToken(access_token);
            setUser({ ...userData, role: userType });

            console.log('Auth state updated:', { token: access_token, user: { ...userData, role: userType } });

            return { success: true, role: userType };
        } catch (error) {
            console.error('Login error:', error);
            return {
                success: false,
                error: error.response?.data?.detail || 'Login failed'
            };
        }
    };

    const logout = () => {
        sessionStorage.removeItem('token');
        sessionStorage.removeItem('user');
        setToken(null);
        setUser(null);
    };

    const value = {
        user,
        token,
        loading,
        isAuthenticated: !!token,
        login,
        logout,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
};
