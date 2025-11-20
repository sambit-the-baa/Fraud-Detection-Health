import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Shield, AlertTriangle, CheckCircle, XCircle, Loader } from 'lucide-react'
import client from '../api/client'

function FraudAnalysis() {
  const { claimId } = useParams()
  const navigate = useNavigate()
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchAnalysis = async () => {
      try {
        const response = await client.post(`/api/claims/${claimId}/analyze-fraud`)
        setAnalysis(response.data)
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to analyze fraud risk.')
      } finally {
        setLoading(false)
      }
    }

    fetchAnalysis()
  }, [claimId])

  const getRiskColor = (level) => {
    switch (level.toLowerCase()) {
      case 'high':
        return 'text-red-600 bg-red-50 border-red-200'
      case 'medium':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'low':
        return 'text-green-600 bg-green-50 border-green-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const getRiskIcon = (level) => {
    switch (level.toLowerCase()) {
      case 'high':
        return <XCircle className="text-red-600" size={24} />
      case 'medium':
        return <AlertTriangle className="text-yellow-600" size={24} />
      case 'low':
        return <CheckCircle className="text-green-600" size={24} />
      default:
        return <Shield className="text-gray-600" size={24} />
    }
  }

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-8 text-center">
          <Loader className="animate-spin text-primary-600 mx-auto mb-4" size={48} />
          <p className="text-gray-600">Analyzing fraud risk...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-3xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">{error}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="bg-white rounded-lg shadow-lg p-8">
        <div className="flex items-center gap-3 mb-6">
          <Shield className="text-primary-600" size={28} />
          <h2 className="text-2xl font-semibold text-gray-800">
            Fraud Risk Analysis
          </h2>
        </div>

        {analysis && (
          <div className="space-y-6">
            {/* Risk Score Card */}
            <div className={`p-6 rounded-lg border-2 ${getRiskColor(analysis.risk_level)}`}>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  {getRiskIcon(analysis.risk_level)}
                  <h3 className="text-xl font-semibold">Risk Level: {analysis.risk_level.toUpperCase()}</h3>
                </div>
                <div className="text-right">
                  <p className="text-3xl font-bold">{analysis.fraud_score.toFixed(1)}</p>
                  <p className="text-sm opacity-75">Fraud Score</p>
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className={`h-3 rounded-full ${
                    analysis.risk_level === 'high' ? 'bg-red-600' :
                    analysis.risk_level === 'medium' ? 'bg-yellow-600' : 'bg-green-600'
                  }`}
                  style={{ width: `${analysis.fraud_score}%` }}
                />
              </div>
              <p className="mt-2 text-sm opacity-75">
                Confidence: {(analysis.confidence * 100).toFixed(1)}%
              </p>
            </div>

            {/* Fraud Indicators */}
            {analysis.indicators.length > 0 && (
              <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
                <h3 className="font-semibold text-red-800 mb-3 flex items-center gap-2">
                  <AlertTriangle size={20} />
                  Fraud Indicators Detected
                </h3>
                <ul className="space-y-2">
                  {analysis.indicators.map((indicator, index) => (
                    <li key={index} className="text-sm text-red-700 flex items-start gap-2">
                      <span className="text-red-600 mt-1">•</span>
                      <span>{indicator}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Recommendations */}
            {analysis.recommendations.length > 0 && (
              <div className="p-6 bg-blue-50 border border-blue-200 rounded-lg">
                <h3 className="font-semibold text-blue-800 mb-3 flex items-center gap-2">
                  <CheckCircle size={20} />
                  Recommendations
                </h3>
                <ul className="space-y-2">
                  {analysis.recommendations.map((rec, index) => (
                    <li key={index} className="text-sm text-blue-700 flex items-start gap-2">
                      <span className="text-blue-600 mt-1">•</span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Next Steps */}
            <div className="p-6 bg-gray-50 border border-gray-200 rounded-lg">
              <h3 className="font-semibold text-gray-800 mb-3">Next Steps</h3>
              <p className="text-sm text-gray-700 mb-4">
                Your claim has been submitted and analyzed. Our team will review the findings and contact you if any additional information is required. 
                You will receive updates via email regarding the status of your claim.
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => navigate(`/claim/${claimId}/success`)}
                  className="flex-1 bg-primary-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-primary-700 transition-colors"
                >
                  Complete Submission
                </button>
                <button
                  onClick={() => navigate(`/claim/${claimId}/details`)}
                  className="flex-1 bg-gray-200 text-gray-800 py-2 px-4 rounded-lg font-medium hover:bg-gray-300 transition-colors"
                >
                  View Claim Details
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default FraudAnalysis

