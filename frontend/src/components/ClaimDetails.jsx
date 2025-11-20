import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, FileText, Calendar, User, Shield, File, MessageCircle, CheckCircle, XCircle, Clock, Download } from 'lucide-react'
import client from '../api/client'

function ClaimDetails() {
  const { claimId } = useParams()
  const navigate = useNavigate()
  const [claim, setClaim] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadClaimDetails()
  }, [claimId])

  const loadClaimDetails = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await client.get(`/api/claims/${claimId}`)
      setClaim(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load claim details')
    } finally {
      setLoading(false)
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'approved':
        return <CheckCircle className="text-green-600" size={24} />
      case 'rejected':
        return <XCircle className="text-red-600" size={24} />
      case 'under_review':
        return <Clock className="text-yellow-600" size={24} />
      default:
        return <Clock className="text-blue-600" size={24} />
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

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading claim details...</p>
        </div>
      </div>
    )
  }

  if (error || !claim) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">{error || 'Claim not found'}</p>
            <button
              onClick={() => navigate(-1)}
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
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-800 mb-4"
        >
          <ArrowLeft size={20} />
          Back
        </button>
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-800">Claim Details</h1>
          <div className={`px-4 py-2 rounded-lg border flex items-center gap-2 ${getStatusColor(claim.status)}`}>
            {getStatusIcon(claim.status)}
            <span className="font-semibold">{formatStatus(claim.status)}</span>
          </div>
        </div>
      </div>

      {/* Claim Information */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Claim Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="flex items-start gap-3">
            <FileText className="text-primary-600 mt-1" size={20} />
            <div>
              <p className="text-sm text-gray-600">Claim Type</p>
              <p className="font-semibold text-gray-800">{claim.claim_type}</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <Calendar className="text-primary-600 mt-1" size={20} />
            <div>
              <p className="text-sm text-gray-600">Incident Date</p>
              <p className="font-semibold text-gray-800">
                {new Date(claim.incident_date).toLocaleDateString()}
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <User className="text-primary-600 mt-1" size={20} />
            <div>
              <p className="text-sm text-gray-600">Policy Number</p>
              <p className="font-semibold text-gray-800">{claim.policy_number}</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <Calendar className="text-primary-600 mt-1" size={20} />
            <div>
              <p className="text-sm text-gray-600">Submitted</p>
              <p className="font-semibold text-gray-800">
                {new Date(claim.created_at).toLocaleString()}
              </p>
            </div>
          </div>
        </div>
        {claim.description && (
          <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-sm text-gray-600 mb-2">Description</p>
            <p className="text-gray-800">{claim.description}</p>
          </div>
        )}
      </div>

      {/* Fraud Analysis */}
      {claim.fraud_score !== null && (
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <Shield className="text-primary-600" size={24} />
            <h2 className="text-xl font-semibold text-gray-800">Fraud Risk Analysis</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600 mb-1">Risk Score</p>
              <p className="text-3xl font-bold text-gray-800">{claim.fraud_score.toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Risk Level</p>
              <span className={`px-3 py-1 rounded text-sm font-semibold ${
                claim.fraud_risk_level === 'high' ? 'bg-red-100 text-red-800' :
                claim.fraud_risk_level === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                'bg-green-100 text-green-800'
              }`}>
                {claim.fraud_risk_level?.toUpperCase()}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Documents */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <div className="flex items-center gap-3 mb-4">
          <File className="text-primary-600" size={24} />
          <h2 className="text-xl font-semibold text-gray-800">
            Documents ({claim.documents.length})
          </h2>
        </div>
        {claim.documents.length === 0 ? (
          <p className="text-gray-600">No documents uploaded</p>
        ) : (
          <div className="space-y-2">
            {claim.documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <File className="text-gray-400" size={20} />
                  <div>
                    <p className="font-medium text-gray-800">{doc.filename}</p>
                    <p className="text-sm text-gray-600">
                      {doc.document_type} • {new Date(doc.uploaded_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <a
                  href={`/api/claims/${claimId}/documents/${doc.id}/download`}
                  download
                  className="text-primary-600 hover:text-primary-800 flex items-center gap-2 px-3 py-1 rounded hover:bg-primary-50 transition-colors"
                >
                  <Download size={16} />
                  Download
                </a>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* AI Questions */}
      {claim.questions_count > 0 && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <MessageCircle className="text-primary-600" size={24} />
            <h2 className="text-xl font-semibold text-gray-800">
              AI Questions ({claim.questions_count})
            </h2>
          </div>
          <p className="text-gray-600">
            This claim has been reviewed through AI-powered questioning. 
            {claim.questions_count} questions were asked and answered.
          </p>
        </div>
      )}
    </div>
  )
}

export default ClaimDetails

