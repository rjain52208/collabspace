import React, { useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import './Auth.css';

const Login = () => {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [isRegister, setIsRegister] = useState(false);
  const { login, register } = useContext(AuthContext);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      if (isRegister) {
        await register({ ...credentials, email: credentials.username + '@example.com' });
        alert('Registration successful! Please login.');
        setIsRegister(false);
      } else {
        await login(credentials);
        window.location.href = '/';
      }
    } catch (err) {
      // Handle different error formats
      const errorData = err.response?.data;
      if (errorData) {
        if (errorData.detail) {
          setError(errorData.detail);
        } else if (errorData.username) {
          setError(errorData.username[0]);
        } else if (errorData.email) {
          setError(errorData.email[0]);
        } else if (errorData.password) {
          setError(errorData.password[0]);
        } else {
          setError(JSON.stringify(errorData));
        }
      } else {
        setError('Authentication failed. Please try again.');
      }
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1>CollabSpace</h1>
        <h2>{isRegister ? 'Register' : 'Login'}</h2>
        
        {error && <div className="alert alert-error">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input
              type="text"
              className="form-control"
              value={credentials.username}
              onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
              required
            />
          </div>
          
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              className="form-control"
              value={credentials.password}
              onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
              required
            />
          </div>
          
          <button type="submit" className="btn btn-primary btn-block">
            {isRegister ? 'Register' : 'Login'}
          </button>
        </form>
        
        <p className="toggle-auth">
          {isRegister ? 'Already have an account?' : "Don't have an account?"}
          <button onClick={() => setIsRegister(!isRegister)} className="link-btn">
            {isRegister ? 'Login' : 'Register'}
          </button>
        </p>
      </div>
    </div>
  );
};

export default Login;
