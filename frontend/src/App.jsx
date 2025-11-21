import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import PolicyEntry from './components/PolicyEntry'
import Dashboard from './components/Dashboard'
import ClaimForm from './components/ClaimForm'
import ClaimDetails from './components/ClaimDetails'
import DocumentUpload from './components/DocumentUpload'
import AIQuestioning from './components/AIQuestioning'
import FraudAnalysis from './components/FraudAnalysis'
import ClaimSuccess from './components/ClaimSuccess'
import logo from './assets/images/logo.png'
import './App.css'
import React, { useState } from 'react';
import client from './api/client';

function App() {
  const [policyNumber, setPolicyNumber] = useState('');
  const [result, setResult] = useState('');

  async function verifyPolicy(policyNumber) {
    try {
      const response = await client.post('/api/verify-policy', { policyNumber });
      setResult(JSON.stringify(response.data));
    } catch (err) {
      setResult('Verification failed! Try again.');
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

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="container mx-auto px-4 py-8">
          <header className="mb-8 text-center">
            <div className="flex justify-center items-center gap-4 mb-4">
              <img 
                src={logo} 
                alt="Company Logo" 
                className="h-64 w-auto object-contain"
              />
            </div>
            <h1 className="text-4xl font-bold text-gray-800 mb-2">
              Health Insurance Claim Portal
            </h1>
            <p className="text-gray-600">
              Submit and track your health insurance claims
            </p>
          </header>

          <Routes>
            <Route path="/" element={<PolicyEntry />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/claim/:policyNumber" element={<ClaimForm />} />
            <Route path="/claim/:claimId/details" element={<ClaimDetails />} />
            <Route path="/claim/:claimId/documents" element={<DocumentUpload />} />
            <Route path="/claim/:claimId/questions" element={<AIQuestioning />} />
            <Route path="/claim/:claimId/analysis" element={<FraudAnalysis />} />
            <Route path="/claim/:claimId/success" element={<ClaimSuccess />} />
          </Routes>
        </div>
      </div>
    </Router>
  )
}

export default App

