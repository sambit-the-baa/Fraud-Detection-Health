import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { FileText, Clock, CheckCircle, XCircle, AlertCircle, Search, Plus } from 'lucide-react'
import client from '../api/client'

function Dashboard() {
  const [searchParams] = useSearchParams()
  const policyNumber = searchParams.get('policy')
  const navigate = useNavigate()
  const [claims, setClaims] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [policyData, setPolicyData] = useState(null)

  useEffect(() => {
    if (policyNumber) {
      loadData()
    }
  }, [policyNumber])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      // Get policy info
      const policyRes = await client.post('/api/verify-policy', {
        policy_number: policyNumber
      })
      setPolicyData(policyRes.data)

      // Get claims
      const claimsRes = await client.get(`/api/policies/${policyNumber}/claims`)
      setClaims(claimsRes.data.claims)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'approved':
        return <CheckCircle className="text-green-600" size={20} />
      case 'rejected':
        return <XCircle className="text-red-600" size={20} />
      case 'under_review':
        return <Clock className="text-yellow-600" size={20} />
      default:
        return <AlertCircle className="text-blue-600" size={20} />
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'approved':
        return 'bg-green-50 border-green-200 text-green-800'
      case 'rejected':
        return 'bg-red-50 border-red-200 text-red-800'
      case 'under_review':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800'
      default:
        return 'bg-blue-50 border-blue-200 text-blue-800'
    }
  }

  const formatStatus = (status) => {
    return status.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ')
  }

  if (!policyNumber) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-8 text-center">
          <Search className="mx-auto text-gray-400 mb-4" size={48} />
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">
            Enter Policy Number
          </h2>
          <p className="text-gray-600 mb-6">
            Please enter your policy number to view your claims dashboard
          </p>
          <button
            onClick={() => navigate('/')}
            className="bg-primary-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-primary-700 transition-colors"
          >
            Go to Policy Entry
          </button>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading your claims...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">{error}</p>
            <button
              onClick={() => navigate('/')}
              className="mt-4 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
            >
              Go Back
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Policy Info Card */}
      {policyData && (
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">Policy Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-600">Policy Number</p>
              <p className="font-semibold text-gray-800">{policyData.policy_number}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Policy Holder</p>
              <p className="font-semibold text-gray-800">{policyData.policy_holder_name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Policy Type</p>
              <p className="font-semibold text-gray-800">{policyData.policy_type}</p>
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="mb-6 flex justify-between items-center">
        <h2 className="text-2xl font-semibold text-gray-800">Your Claims</h2>
        <button
          onClick={() => navigate(`/claim/${policyNumber}`)}
          className="bg-primary-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-primary-700 transition-colors flex items-center gap-2"
        >
          <Plus size={20} />
          New Claim
        </button>
      </div>

      {/* Claims List */}
      {claims.length === 0 ? (
        <div className="bg-white rounded-lg shadow-lg p-12 text-center">
          <FileText className="mx-auto text-gray-400 mb-4" size={64} />
          <h3 className="text-xl font-semibold text-gray-800 mb-2">No Claims Found</h3>
          <p className="text-gray-600 mb-6">
            You haven't submitted any claims yet. Start by creating a new claim.
          </p>
          <button
            onClick={() => navigate(`/claim/${policyNumber}`)}
            className="bg-primary-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-primary-700 transition-colors"
          >
            Create Your First Claim
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {claims.map((claim) => (
            <div
              key={claim.id}
              className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow cursor-pointer"
              onClick={() => navigate(`/claim/${claim.id}/details`)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <FileText className="text-primary-600" size={24} />
                    <div>
                      <h3 className="text-lg font-semibold text-gray-800">
                        {claim.claim_type}
                      </h3>
                      <p className="text-sm text-gray-600">
                        Claim #{claim.id} • {new Date(claim.incident_date).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">
                    Submitted: {new Date(claim.created_at).toLocaleString()}
                  </p>
                  {claim.fraud_score !== null && (
                    <div className="flex items-center gap-4">
                      <div>
                        <span className="text-xs text-gray-600">Fraud Risk:</span>
                        <span className={`ml-2 px-2 py-1 rounded text-xs font-semibold ${
                          claim.fraud_risk_level === 'high' ? 'bg-red-100 text-red-800' :
                          claim.fraud_risk_level === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-green-100 text-green-800'
                        }`}>
                          {claim.fraud_risk_level?.toUpperCase()} ({claim.fraud_score.toFixed(1)}%)
                        </span>
                      </div>
                    </div>
                  )}
                </div>
                <div className={`px-4 py-2 rounded-lg border flex items-center gap-2 ${getStatusColor(claim.status)}`}>
                  {getStatusIcon(claim.status)}
                  <span className="font-medium">{formatStatus(claim.status)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default Dashboard

