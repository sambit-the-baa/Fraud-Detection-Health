import React, { useState } from 'react';
import client from '../api/client';
import App from './App.jsx';   // must exist in src/
import './index.css';          // must exist in src/

function App() {
  const [policyNumber, setPolicyNumber] = useState('');
  const [result, setResult] = useState('');

  async function verifyPolicy(policyNumber) {
    try {
      const response = await client.post('/api/verify-policy', { policyNumber });
      setResult(JSON.stringify(response.data)); // Show in UI or process accordingly
    } catch (err) {
      setResult('Verification failed! Try again.');
      // Errors already logged
    }
  }

  return (
    <div>
      <h2>Policy Verification</h2>
      <input
        value={policyNumber}
        onChange={e => setPolicyNumber(e.target.value)}
        placeholder="Enter Policy Number"
      />
      <button onClick={() => verifyPolicy(policyNumber)}>
        Verify Policy
      </button>
      <p>Result: {result}</p>
    </div>
  );
}

export default App;
