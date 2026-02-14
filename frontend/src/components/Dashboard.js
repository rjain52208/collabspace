import React, { useState, useEffect, useContext, useRef } from 'react';
import { documentsAPI } from '../services/api';
import { AuthContext } from '../context/AuthContext';
import './Dashboard.css';

const Dashboard = ({ onSelectDocument }) => {
  const [documents, setDocuments] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newDocument, setNewDocument] = useState({ title: '', content: '' });
  const { user, logout } = useContext(AuthContext);
  const wsRef = useRef(null);

  useEffect(() => {
    loadDocuments();
    connectDashboardWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const connectDashboardWebSocket = () => {
    const token = localStorage.getItem('access_token');
    const wsUrl = `ws://localhost:8000/ws/documents/?token=${token}`;
    
    console.log('📡 Connecting to dashboard WebSocket...');
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('✅ Dashboard WebSocket connected');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('📨 Dashboard update:', data);

      if (data.type === 'document_created' || data.type === 'document_shared') {
        console.log('🔄 Reloading documents...');
        loadDocuments();
      }
    };

    ws.onclose = () => {
      console.log('Dashboard WebSocket closed');
    };
  };

  const loadDocuments = async () => {
    try {
      const response = await documentsAPI.getAll();
      setDocuments(response.data);
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
  };

  const handleCreateDocument = async (e) => {
    e.preventDefault();
    try {
      await documentsAPI.create(newDocument);
      setShowCreateModal(false);
      setNewDocument({ title: '', content: '' });
      loadDocuments();
    } catch (error) {
      console.error('Failed to create document:', error);
    }
  };

  const handleDeleteDocument = async (id) => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      try {
        await documentsAPI.delete(id);
        loadDocuments();
      } catch (error) {
        console.error('Failed to delete document:', error);
      }
    }
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>CollabSpace</h1>
        <div className="header-actions">
          <span className="user-info">
            {user?.username} ({user?.role})
          </span>
          <button onClick={logout} className="btn btn-secondary">
            Logout
          </button>
        </div>
      </header>

      <div className="container">
        <div className="dashboard-controls">
          <h2>My Documents</h2>
          <button onClick={() => setShowCreateModal(true)} className="btn btn-primary">
            + New Document
          </button>
        </div>

        <div className="documents-grid">
          {documents.map((doc) => (
            <div key={doc.id} className="document-card">
              <h3>{doc.title}</h3>
              <p className="document-meta">
                Owner: {doc.owner.username}<br />
                Collaborators: {doc.collaborators.length}<br />
                Updated: {new Date(doc.updated_at).toLocaleDateString()}
              </p>
              <div className="document-actions">
                <button
                  onClick={() => onSelectDocument(doc.id)}
                  className="btn btn-primary"
                >
                  Open
                </button>
                {doc.owner.id === user?.id && (
                  <button
                    onClick={() => handleDeleteDocument(doc.id)}
                    className="btn btn-danger"
                  >
                    Delete
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>

        {documents.length === 0 && (
          <div className="empty-state">
            <p>No documents yet. Create your first document to get started!</p>
          </div>
        )}
      </div>

      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Create New Document</h2>
            <form onSubmit={handleCreateDocument}>
              <div className="form-group">
                <label>Title</label>
                <input
                  type="text"
                  className="form-control"
                  value={newDocument.title}
                  onChange={(e) => setNewDocument({ ...newDocument, title: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Initial Content (optional)</label>
                <textarea
                  className="form-control"
                  rows="4"
                  value={newDocument.content}
                  onChange={(e) => setNewDocument({ ...newDocument, content: e.target.value })}
                />
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowCreateModal(false)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
