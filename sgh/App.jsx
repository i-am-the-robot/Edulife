// Main App Component with Routing
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';

// Auth Pages
import TeacherAdminLogin from './pages/auth/Login';

// Student Pages
import StudentLogin from './pages/student/Login';
import StudentDashboard from './pages/student/Dashboard';
import ChatPage from './pages/student/Chat';
import ChatHistory from './pages/student/ChatHistory';
import Achievements from './pages/student/Achievements';
import Schedule from './pages/student/Schedule';

// Teacher Pages
import TeacherDashboard from './pages/teacher/Dashboard';
import TeacherStudents from './pages/teacher/Students';
import StudentProfile from './pages/teacher/StudentProfile';
import TeacherRegister from './pages/teacher/Register';
import TeacherChangePassword from './pages/teacher/ChangePassword';
import TaskScheduler from './pages/teacher/TaskScheduler';
import SyllabusUpload from './pages/teacher/SyllabusUpload';
import StudentTasks from './pages/student/StudentTasks';

// Admin Pages
import AdminDashboard from './pages/admin/Dashboard';
import SchoolsPage from './pages/admin/Schools';
import TeachersPage from './pages/admin/Teachers';
import AdminStudentsPage from './pages/admin/Students';
import ChangePassword from './pages/admin/ChangePassword';

// Protected Route Component
function ProtectedRoute({ children, allowedRole }) {
  const { isAuthenticated, user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRole && user?.role !== allowedRole) {
    return <Navigate to={`/${user?.role}/dashboard`} replace />;
  }

  return children;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Landing/Login */}
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<TeacherAdminLogin />} />
          <Route path="/student/login" element={<StudentLogin />} />

          {/* Student Routes */}
          <Route
            path="/student/dashboard"
            element={
              <ProtectedRoute allowedRole="student">
                <StudentDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/student/chat"
            element={
              <ProtectedRoute allowedRole="student">
                <ChatPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/student/chat-history"
            element={
              <ProtectedRoute allowedRole="student">
                <ChatHistory />
              </ProtectedRoute>
            }
          />
          <Route
            path="/student/achievements"
            element={
              <ProtectedRoute allowedRole="student">
                <Achievements />
              </ProtectedRoute>
            }
          />
          <Route
            path="/student/schedule"
            element={
              <ProtectedRoute allowedRole="student">
                <Schedule />
              </ProtectedRoute>
            }
          />

          {/* Teacher Routes */}
          <Route path="/teacher/register" element={<TeacherRegister />} />
          <Route path="/teacher/dashboard" element={
            <ProtectedRoute allowedRole="teacher">
              <TeacherDashboard />
            </ProtectedRoute>
          } />
          <Route path="/teacher/students" element={
            <ProtectedRoute allowedRole="teacher">
              <TeacherStudents />
            </ProtectedRoute>
          } />
          <Route path="/teacher/students/:studentId" element={
            <ProtectedRoute allowedRole="teacher">
              <StudentProfile />
            </ProtectedRoute>
          } />
          <Route path="/teacher/change-password" element={
            <ProtectedRoute allowedRole="teacher">
              <TeacherChangePassword />
            </ProtectedRoute>
          } />
          <Route path="/teacher/tasks" element={
            <ProtectedRoute allowedRole="teacher">
              <TaskScheduler />
            </ProtectedRoute>
          } />
          <Route path="/teacher/syllabus" element={
            <ProtectedRoute allowedRole="teacher">
              <SyllabusUpload />
            </ProtectedRoute>
          } />
          <Route path="/teacher/register-student" element={
            <ProtectedRoute allowedRole="teacher">
              <AdminStudentsPage />
            </ProtectedRoute>
          } />
          <Route path="/student/tasks" element={
            <ProtectedRoute allowedRole="student">
              <StudentTasks />
            </ProtectedRoute>
          } />

          {/* Admin Routes */}
          <Route
            path="/admin/dashboard"
            element={
              <ProtectedRoute allowedRole="admin">
                <AdminDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/schools"
            element={
              <ProtectedRoute allowedRole="admin">
                <SchoolsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/teachers"
            element={
              <ProtectedRoute allowedRole="admin">
                <TeachersPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/students"
            element={
              <ProtectedRoute allowedRole="admin">
                <AdminStudentsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/change-password"
            element={
              <ProtectedRoute allowedRole="admin">
                <ChangePassword />
              </ProtectedRoute>
            }
          />

          {/* Catch all */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
