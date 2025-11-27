import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { FileText, ArrowRight } from 'lucide-react'
import client from '../api/client'

function ClaimForm() {
  const { policyNumber } = useParams()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [formData, setFormData] = useState({
    claim_type: '',
    incident_date: '',
    description: ''
  })
  const [errors, setErrors] = useState({})

  const validateForm = () => {
    const newErrors = {}
    
    if (!formData.claim_type) {
      newErrors.claim_type = 'Claim type is required'
    }
    
    if (!formData.incident_date) {
      newErrors.incident_date = 'Incident date is required'
    } else {
      // Validate date format
          const dateRegex = /^\d{4}-\d{2}-\d{2}$/
      if (!dateRegex.test(formData.incident_date)) {
        newErrors.incident_date = 'Please select a valid date'
      } else {
        const incidentDate = new Date(formData.incident_date + 'T00:00:00')
        const today = new Date()
        today.setHours(23, 59, 59, 999) // End of today
        if (incidentDate > today) {
          newErrors.incident_date = 'Incident date cannot be in the future'
        }
      }
    }
    
    if (formData.description && formData.description.length > 5000) {
      newErrors.description = 'Description must be less than 5000 characters'
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }
    
    setLoading(true)
    setError(null)
    setErrors({})

    try {
      // Convert date to ISO datetime format for backend
      // HTML date input gives YYYY-MM-DD, backend expects YYYY-MM-DDTHH:MM:SS
      let incidentDateISO = null
      if (formData.incident_date) {
        // Add time component (00:00:00) to make it a valid datetime string
        incidentDateISO = `${formData.incident_date}T00:00:00`
      }

      const response = await client.post('/api/claims', {
        policy_number: policyNumber,
        claim_type: formData.claim_type,
        incident_date: incidentDateISO,
        description: formData.description
      })

      navigate(`/claim/${response.data.id}/documents`)
    } catch (err) {
      if (err.response?.data?.detail) {
        if (Array.isArray(err.response.data.detail)) {
          const validationErrors = {}
          err.response.data.detail.forEach(error => {
            const field = error.loc[error.loc.length - 1]
            validationErrors[field] = error.msg
          })
          setErrors(validationErrors)
        } else {
          setError(err.response.data.detail)
        }
      } else {
        setError(err.response?.data?.message || 'Failed to create claim. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-lg shadow-lg p-8">
        <div className="flex items-center gap-3 mb-6">
          <FileText className="text-primary-600" size={28} />
          <h2 className="text-2xl font-semibold text-gray-800">
            Create New Claim
          </h2>
        </div>

        <p className="text-gray-600 mb-6">
          Policy: <span className="font-semibold">{policyNumber}</span>
        </p>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="claim_type" className="block text-sm font-medium text-gray-700 mb-2">
              Claim Type *
            </label>
            <select
              id="claim_type"
              value={formData.claim_type}
              onChange={(e) => {
                setFormData({ ...formData, claim_type: e.target.value })
                if (errors.claim_type) setErrors({ ...errors, claim_type: '' })
              }}
              className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
                errors.claim_type ? 'border-red-300' : 'border-gray-300'
              }`}
              required
            >
              <option value="">Select claim type</option>
              {errors.claim_type && (
                <span className="text-red-600 text-sm mt-1">{errors.claim_type}</span>
              )}
              <option value="Medical Treatment">Medical Treatment</option>
              <option value="Hospitalization">Hospitalization</option>
              <option value="Surgery">Surgery</option>
              <option value="Emergency">Emergency</option>
              <option value="Prescription">Prescription</option>
              <option value="Other">Other</option>
            </select>
          </div>

          <div>
            <label htmlFor="incident_date" className="block text-sm font-medium text-gray-700 mb-2">
              Incident Date *
            </label>
            <input
              id="incident_date"
              type="date"
              value={formData.incident_date}
              onChange={(e) => {
                setFormData({ ...formData, incident_date: e.target.value })
                if (errors.incident_date) setErrors({ ...errors, incident_date: '' })
              }}
              className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
                errors.incident_date ? 'border-red-300' : 'border-gray-300'
              }`}
              required
            />
            {errors.incident_date && (
              <p className="text-red-600 text-sm mt-1">{errors.incident_date}</p>
            )}
          </div>

          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              id="description"
              value={formData.description}
              onChange={(e) => {
                setFormData({ ...formData, description: e.target.value })
                if (errors.description) setErrors({ ...errors, description: '' })
              }}
              rows={4}
              placeholder="Please provide details about the incident or treatment..."
              maxLength={5000}
              className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
                errors.description ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            <div className="flex justify-between items-center mt-1">
              {errors.description && (
                <p className="text-red-600 text-sm">{errors.description}</p>
              )}
              <p className="text-gray-500 text-sm ml-auto">
                {formData.description.length}/5000 characters
              </p>
            </div>
          </div>

          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? 'Creating Claim...' : 'Continue to Document Upload'}
            <ArrowRight size={20} />
          </button>
        </form>
      </div>
    </div>
  )
}

export default ClaimForm

