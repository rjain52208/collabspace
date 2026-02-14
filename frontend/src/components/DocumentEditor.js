import React, { useState, useEffect, useRef, useContext } from 'react';
import { documentsAPI } from '../services/api';
import { AuthContext } from '../context/AuthContext';
import './DocumentEditor.css';

const DocumentEditor = ({ documentId, onBack }) => {
  const [document, setDocument] = useState(null);
  const [content, setContent] = useState('');
  const [saving, setSaving] = useState(false);
  const [connected, setConnected] = useState(false);
  const [activeUsers, setActiveUsers] = useState([]);
  const { user } = useContext(AuthContext);
  const wsRef = useRef(null);

  useEffect(() => {
    loadDocument();
    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []); // Run once on mount

  const loadDocument = async () => {
    try {
      const response = await documentsAPI.getById(documentId);
      setDocument(response.data);
      setContent(response.data.content);
    } catch (error) {
      console.error('Failed to load document:', error);
    }
  };

  const connectWebSocket = () => {
    const token = localStorage.getItem('access_token');
    const WS_URL = 'ws://localhost:8000';
    const wsUrl = `${WS_URL}/ws/document/${documentId}/?token=${token}`;

    console.log('Connecting to:', wsUrl);
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket OPENED');
      setConnected(true);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('Received:', data);

      if (data.type === 'user_joined') {
        setActiveUsers(prev => [...new Set([...prev, data.user])]);
      } else if (data.type === 'user_left') {
        setActiveUsers(prev => prev.filter(u => u !== data.user));
      } else if (data.type === 'edit' && data.user !== user?.username) {
        // Apply remote edits only
        setContent(current => {
          if (data.operation === 'insert') {
            return current.slice(0, data.position) + data.content + current.slice(data.position);
          } else if (data.operation === 'delete') {
            return current.slice(0, data.position) + current.slice(data.position + 1);
          }
          return current;
        });
      }
    };

    ws.onclose = () => {
      console.log('WebSocket CLOSED');
      setConnected(false);
    };

    ws.onerror = (error) => {
      console.error('WebSocket ERROR:', error);
    };
  };

  const handleChange = (e) => {
    const newContent = e.target.value;
    const cursorPos = e.target.selectionStart;

    if (newContent.length > content.length && wsRef.current?.readyState === 1) {
      // Insert
      const pos = cursorPos - 1;
      const char = newContent.charAt(pos);
      wsRef.current.send(JSON.stringify({
        type: 'edit',
        operation: 'insert',
        position: pos,
        content: char,
        version: document?.version || 1
      }));
    } else if (newContent.length < content.length && wsRef.current?.readyState === 1) {
      // Delete
      wsRef.current.send(JSON.stringify({
        type: 'edit',
        operation: 'delete',
        position: cursorPos,
        content: '',
        version: document?.version || 1
      }));
    }

    setContent(newContent);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await documentsAPI.update(documentId, { content });
      alert('Saved!');
    } catch (error) {
      alert('Save failed');
    } finally {
      setSaving(false);
    }
  };

  if (!document) return <div className="loading">Loading...</div>;

  return (
    <div className="editor-container">
      <header className="editor-header">
        <div className="editor-title">
          <button onClick={onBack} className="btn btn-secondary">← Back</button>
          <h2>{document.title}</h2>
          <span className={`connection-status ${connected ? 'connected' : 'disconnected'}`}>
            {connected ? '● Connected' : '○ Disconnected'}
          </span>
        </div>
        <div className="editor-actions">
          <button onClick={handleSave} className="btn btn-success" disabled={saving}>
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </header>

      <div className="editor-info">
        <div className="active-users">
          <strong>Active Users:</strong> {activeUsers.join(', ') || 'Only you'}
        </div>
      </div>

      <div className="editor-content">
        <textarea
          className="editor-textarea"
          value={content}
          onChange={handleChange}
          placeholder="Start typing..."
        />
      </div>

      <div className="editor-footer">
        <span>Version: {document.version}</span>
        <span>Characters: {content.length}</span>
      </div>
    </div>
  );
};

export default DocumentEditor;
