import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { CheckCircle, FileText, ArrowRight, Home } from 'lucide-react'

function ClaimSuccess() {
  const { claimId } = useParams()
  const navigate = useNavigate()

  useEffect(() => {
    // Auto-redirect after 10 seconds
    const timer = setTimeout(() => {
      navigate(`/claim/${claimId}/details`)
    }, 10000)

    return () => clearTimeout(timer)
  }, [claimId, navigate])

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-lg shadow-lg p-12 text-center">
        <div className="mb-6">
          <div className="mx-auto w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mb-4">
            <CheckCircle className="text-green-600" size={48} />
          </div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            Claim Submitted Successfully!
          </h1>
          <p className="text-gray-600">
            Your claim has been received and is being processed
          </p>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6 text-left">
          <div className="flex items-start gap-3">
            <FileText className="text-blue-600 flex-shrink-0 mt-1" size={20} />
            <div>
              <h3 className="font-semibold text-blue-800 mb-2">What's Next?</h3>
              <ul className="text-sm text-blue-700 space-y-2">
                <li>• Your claim has been assigned ID: <strong>#{claimId}</strong></li>
                <li>• Our team will review your submission and documents</li>
                <li>• You'll receive updates on the status of your claim</li>
                <li>• Fraud analysis has been completed automatically</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={() => navigate(`/claim/${claimId}/details`)}
            className="bg-primary-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-primary-700 transition-colors flex items-center justify-center gap-2"
          >
            View Claim Details
            <ArrowRight size={20} />
          </button>
          <button
            onClick={() => navigate('/')}
            className="bg-gray-200 text-gray-800 px-6 py-3 rounded-lg font-medium hover:bg-gray-300 transition-colors flex items-center justify-center gap-2"
          >
            <Home size={20} />
            Back to Home
          </button>
        </div>

        <p className="mt-6 text-sm text-gray-500">
          Redirecting to claim details in a few seconds...
        </p>
      </div>
    </div>
  )
}

export default ClaimSuccess

