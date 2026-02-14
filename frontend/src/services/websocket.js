class WebSocketService {
  constructor() {
    this.ws = null;
    this.documentId = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.listeners = {};
  }

  connect(documentId) {
    // If already connected to this document, don't reconnect
    if (this.ws && this.ws.readyState === WebSocket.OPEN && this.documentId === documentId) {
      console.log('Already connected to document', documentId);
      return;
    }
    
    // Close existing connection if any
    if (this.ws) {
      this.ws.close();
    }
    
    const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';
    const token = localStorage.getItem('access_token');
    
    if (!token) {
      console.error('No authentication token found');
      return;
    }

    this.documentId = documentId;
    const wsUrl = `${WS_URL}/ws/document/${documentId}/?token=${token}`;
    
    console.log('Connecting to WebSocket:', wsUrl);
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.trigger('connected');
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.trigger('message', data);
      
      // Trigger specific event types
      if (data.type) {
        this.trigger(data.type, data);
      }
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.trigger('disconnected');
      this.attemptReconnect();
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.trigger('error', error);
    };
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.reconnectAttempts = this.maxReconnectAttempts;
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts && this.documentId) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      setTimeout(() => {
        this.connect(this.documentId);
      }, 1000 * this.reconnectAttempts);
    }
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.error('WebSocket is not connected');
    }
  }

  // Event handling with proper cleanup
  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  off(event, callback) {
    if (!this.listeners[event]) return;
    
    if (callback) {
      // Remove specific callback
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    } else {
      // Remove all callbacks for this event
      this.listeners[event] = [];
    }
  }

  trigger(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => callback(data));
    }
  }

  clearAllListeners() {
    this.listeners = {};
  }

  // Document operations
  sendEdit(operation, position, content, version) {
    this.send({
      type: 'edit',
      operation,
      position,
      content,
      version,
      timestamp: Date.now(),
    });
  }

  sendCursorPosition(position) {
    this.send({
      type: 'cursor',
      position,
    });
  }

  sendLock(section, locked) {
    this.send({
      type: 'lock',
      section,
      locked,
    });
  }
}

export default new WebSocketService();
