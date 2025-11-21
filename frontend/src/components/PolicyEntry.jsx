import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, AlertCircle, CheckCircle } from 'lucide-react'
import client from '../api/client'

function PolicyEntry() {
  const [policyNumber, setPolicyNumber] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [policyData, setPolicyData] = useState(null)
  const navigate = useNavigate()

  const handleVerify = async (e) => {
    e.preventDefault()
    console.log('Form submitted, policyNumber:', policyNumber)
    setLoading(true)
    setError(null)
    setPolicyData(null)

    try {
      const response = await client.post('/api/verify-policy', {
        policy_number: policyNumber.trim()
      })
      console.log('API response:', response.data)
      if (response.data?.valid) {
        setPolicyData(response.data)
      } else {
        setError('Policy not found or invalid. Please check your policy number.')
      }
    } catch (err) {
      console.error('API error:', err)
      setError(
        err.response?.data?.detail || 
        'Policy not found or server error. Please check your policy number.'
      )
    } finally {
      setLoading(false)
    }
  }

  const handleContinue = () => {
    if (policyData && policyData.policy_number) {
      navigate(`/claim/${policyData.policy_number}`)
    }
  }

  const handleViewDashboard = () => {
    if (policyData && policyData.policy_number) {
      navigate(`/dashboard?policy=${policyData.policy_number}`)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-lg shadow-lg p-8">
        <h2 className="text-2xl font-semibold text-gray-800 mb-6">
          Enter Your Policy Number
        </h2>
        <form onSubmit={handleVerify} className="space-y-6">
          <div>
            <label htmlFor="policy" className="block text-sm font-medium text-gray-700 mb-2">
              Policy Number
            </label>
            <div className="relative">
              <input
                id="policy"
                type="text"
                value={policyNumber}
                onChange={(e) => setPolicyNumber(e.target.value)}
                placeholder="e.g., POL-2024-001"
                className="w-full px-4 py-3 pl-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                required
                disabled={loading}
              />
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            </div>
          </div>
          <button
            type="submit"
            disabled={loading || !policyNumber.trim()}
            className="w-full bg-primary-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Verifying...' : 'Verify Policy'}
          </button>
        </form>

        {error && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <AlertCircle className="text-red-600 flex-shrink-0 mt-0.5" size={20} />
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}

        {policyData && (
          <div className="mt-6 p-6 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-start gap-3 mb-4">
              <CheckCircle className="text-green-600 flex-shrink-0" size={24} />
              <div className="flex-1">
                <h3 className="font-semibold text-green-800 mb-2">Policy Verified</h3>
                <div className="space-y-2 text-sm text-green-700">
                  <p><strong>Policy Holder:</strong> {policyData.policy_holder_name}</p>
                  <p><strong>Policy Type:</strong> {policyData.policy_type}</p>
                  {policyData.expiry_date && (
                    <p><strong>Expiry Date:</strong> {new Date(policyData.expiry_date).toLocaleDateString()}</p>
                  )}
                </div>
              </div>
            </div>
            <div className="flex gap-3">
              <button
                onClick={handleContinue}
                className="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-green-700 transition-colors"
              >
                New Claim
              </button>
              <button
                onClick={handleViewDashboard}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-blue-700 transition-colors"
              >
                View Dashboard
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default PolicyEntry
