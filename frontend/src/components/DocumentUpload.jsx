import { useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Upload, File, X, ArrowRight, CheckCircle } from 'lucide-react'
import client from '../api/client'

function DocumentUpload() {
  const { claimId } = useParams()
  const navigate = useNavigate()
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState({})
  const [uploaded, setUploaded] = useState([])
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files)
    const maxSize = 10 * 1024 * 1024 // 10MB
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    
    const validFiles = []
    const errors = []
    
    selectedFiles.forEach(file => {
      if (file.size > maxSize) {
        errors.push(`${file.name}: File size exceeds 10MB`)
      } else if (!allowedTypes.includes(file.type)) {
        errors.push(`${file.name}: File type not allowed`)
      } else {
        validFiles.push(file)
      }
    })
    
    if (errors.length > 0) {
      setError(errors.join('; '))
    }
    
    setFiles(prev => [...prev, ...validFiles])
  }

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const handleUpload = async () => {
    if (files.length === 0) {
      setError('Please select at least one file to upload')
      return
    }

    setUploading(true)
    setError(null)

    try {
      const uploadPromises = files.map(async (file, index) => {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('document_type', file.name)

        setUploadProgress(prev => ({ ...prev, [index]: 0 }))

        const response = await client.post(
          `/api/claims/${claimId}/documents`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
            onUploadProgress: (progressEvent) => {
              const percentCompleted = Math.round(
                (progressEvent.loaded * 100) / progressEvent.total
              )
              setUploadProgress(prev => ({ ...prev, [index]: percentCompleted }))
            },
          }
        )
        setUploadProgress(prev => ({ ...prev, [index]: 100 }))
        return response.data
      })

      const results = await Promise.all(uploadPromises)
      setUploaded(results)
      setFiles([])
      setUploadProgress({})
    } catch (err) {
      setError(err.response?.data?.detail || err.response?.data?.message || 'Failed to upload documents. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  const handleContinue = () => {
    navigate(`/claim/${claimId}/questions`)
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="bg-white rounded-lg shadow-lg p-8">
        <h2 className="text-2xl font-semibold text-gray-800 mb-6">
          Upload Documents
        </h2>

        <p className="text-gray-600 mb-6">
          Please upload all relevant documents for your claim (medical reports, prescriptions, invoices, etc.)
        </p>

        <div className="mb-6">
          <div
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-primary-500 hover:bg-primary-50 transition-colors"
          >
            <Upload className="mx-auto text-gray-400 mb-4" size={48} />
            <p className="text-gray-600 mb-2">Click to select files or drag and drop</p>
            <p className="text-sm text-gray-500">PDF, JPG, PNG up to 10MB each</p>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            onChange={handleFileSelect}
            className="hidden"
            accept=".pdf,.jpg,.jpeg,.png"
          />
        </div>

        {files.length > 0 && (
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-700 mb-3">Selected Files:</h3>
            <div className="space-y-2">
              {files.map((file, index) => (
                <div
                  key={index}
                  className="flex flex-col gap-2 p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <File className="text-gray-400" size={20} />
                      <span className="text-sm text-gray-700">{file.name}</span>
                      <span className="text-xs text-gray-500">
                        ({(file.size / 1024 / 1024).toFixed(2)} MB)
                      </span>
                    </div>
                    <button
                      onClick={() => removeFile(index)}
                      className="text-red-600 hover:text-red-800"
                    >
                      <X size={20} />
                    </button>
                  </div>
                  {uploadProgress[index] !== undefined && (
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${uploadProgress[index]}%` }}
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="mt-4 w-full bg-primary-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-primary-700 transition-colors disabled:opacity-50"
            >
              {uploading ? 'Uploading...' : `Upload ${files.length} File(s)`}
            </button>
          </div>
        )}

        {uploaded.length > 0 && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center gap-2 mb-3">
              <CheckCircle className="text-green-600" size={20} />
              <h3 className="font-semibold text-green-800">Uploaded Documents:</h3>
            </div>
            <ul className="space-y-2">
              {uploaded.map((doc, index) => (
                <li key={index} className="text-sm text-green-700 flex items-center gap-2">
                  <File size={16} />
                  {doc.filename}
                </li>
              ))}
            </ul>
          </div>
        )}

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}

        <div className="flex gap-4">
          <button
            onClick={handleContinue}
            disabled={uploaded.length === 0}
            className="flex-1 bg-primary-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            Continue to AI Questions
            <ArrowRight size={20} />
          </button>
        </div>
      </div>
    </div>
  )
}

export default DocumentUpload

