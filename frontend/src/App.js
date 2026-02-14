import React, { useContext, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, AuthContext } from './context/AuthContext';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import DocumentEditor from './components/DocumentEditor';

const PrivateRoute = ({ children }) => {
  const { user, loading } = useContext(AuthContext);

  if (loading) {
    return <div>Loading...</div>;
  }

  return user ? children : <Navigate to="/login" />;
};

const AppContent = () => {
  const { user } = useContext(AuthContext);
  const [selectedDocument, setSelectedDocument] = useState(null);

  if (!user) {
    return <Login />;
  }

  if (selectedDocument) {
    return (
      <DocumentEditor
        documentId={selectedDocument}
        onBack={() => setSelectedDocument(null)}
      />
    );
  }

  return <Dashboard onSelectDocument={setSelectedDocument} />;
};

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
