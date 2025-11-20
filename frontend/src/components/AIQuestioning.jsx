import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { MessageCircle, Send, ArrowRight, Loader } from 'lucide-react'
import client from '../api/client'

function AIQuestioning() {
  const { claimId } = useParams()
  const navigate = useNavigate()
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [questionCount, setQuestionCount] = useState(0) // Tracks completed Q&A pairs
  const [autoAnalyzing, setAutoAnalyzing] = useState(false)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    // Initial AI greeting with contextual first question
    loadInitialQuestion()
  }, [claimId])

  const loadInitialQuestion = async () => {
    try {
      // Get claim details to ask contextual first question
      const claimResponse = await client.get(`/api/claims/${claimId}`)
      const claim = claimResponse.data
      
      // Generate contextual first question based on claim type
      const firstQuestion = getContextualFirstQuestion(claim)
      
      setMessages([{
        type: 'ai',
        content: `Hello! I'm here to help process your ${claim.claim_type} claim. ${firstQuestion}`
      }])
    } catch (err) {
      // Fallback if claim details can't be loaded
      setMessages([{
        type: 'ai',
        content: 'Hello! I\'m here to help process your claim. I\'ll ask you some questions about the incident to ensure we have all the necessary information. Please provide as much detail as possible.'
      }])
    }
  }

  const getContextualFirstQuestion = (claim) => {
    const claimType = claim.claim_type.toLowerCase()
    
    if (claimType.includes('hospitalization') || claimType.includes('surgery')) {
      return 'Can you please tell me when you were admitted to the hospital and what was the primary reason for your admission?'
    } else if (claimType.includes('emergency')) {
      return 'Can you describe what happened during the emergency incident? When did it occur?'
    } else if (claimType.includes('prescription')) {
      return 'Can you tell me about the medication you were prescribed? What condition was it treating?'
    } else if (claimType.includes('medical treatment')) {
      return 'Can you describe the medical treatment you received? When did you start this treatment?'
    } else {
      return 'Can you please provide more details about the incident? When did it occur and what happened?'
    }
  }

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading || autoAnalyzing) return

    const userMessage = input.trim()
    setInput('')
    setMessages(prev => [...prev, { type: 'user', content: userMessage }])
    setLoading(true)
    setError(null)

    try {
      const response = await client.post(
        `/api/claims/${claimId}/ask-question`,
        { user_message: userMessage }
      )

      const newQuestionCount = questionCount + 1
      setQuestionCount(newQuestionCount)

      setMessages(prev => [...prev, {
        type: 'ai',
        content: response.data.ai_message,
        followUpQuestions: response.data.follow_up_questions,
        fraudIndicators: response.data.fraud_indicators
      }])

      // After 3-4 questions answered, automatically proceed to fraud analysis
      if (newQuestionCount >= 3) {
        setAutoAnalyzing(true)
        setLoading(true)
        setMessages(prev => [...prev, {
          type: 'ai',
          content: 'Thank you for providing all that information. I have enough details now. Let me analyze your claim for fraud risk...'
        }])
        
        // Trigger fraud analysis
        try {
          await client.post(`/api/claims/${claimId}/analyze-fraud`)
          // Navigate to analysis page after a brief delay
          setTimeout(() => {
            navigate(`/claim/${claimId}/analysis`)
          }, 2000)
        } catch (err) {
          console.error('Error analyzing fraud:', err)
          // Still navigate even if analysis fails
          setTimeout(() => {
            navigate(`/claim/${claimId}/analysis`)
          }, 1000)
        }
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send message. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleContinue = async () => {
    setLoading(true)
    setError(null)
    
    // Trigger fraud analysis before navigating
    try {
      await client.post(`/api/claims/${claimId}/analyze-fraud`)
      // Navigate to analysis page
      navigate(`/claim/${claimId}/analysis`)
    } catch (err) {
      console.error('Error analyzing fraud:', err)
      setError(err.response?.data?.detail || 'Failed to analyze fraud. Please try again.')
      setLoading(false)
      // Still navigate even if analysis fails - let the analysis page handle it
      setTimeout(() => {
        navigate(`/claim/${claimId}/analysis`)
      }, 2000)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-lg p-8">
        <div className="flex items-center gap-3 mb-6">
          <MessageCircle className="text-primary-600" size={28} />
          <h2 className="text-2xl font-semibold text-gray-800">
            AI-Assisted Claim Review
          </h2>
        </div>

        <div className="mb-6">
          <p className="text-gray-600 mb-2">
            Our AI will ask you 3-4 contextual questions about your claim to gather necessary information.
          </p>
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <div className="flex-1 bg-gray-200 rounded-full h-2">
              <div 
                className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${Math.min((questionCount / 4) * 100, 100)}%` }}
              />
            </div>
            <span className="text-xs font-medium">
              {questionCount}/3-4 questions answered
            </span>
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-6 mb-6 h-96 overflow-y-auto">
          <div className="space-y-4">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-4 ${
                    msg.type === 'user'
                      ? 'bg-primary-600 text-white'
                      : 'bg-white border border-gray-200 text-gray-800'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                  {msg.fraudIndicators && msg.fraudIndicators.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-red-200">
                      <p className="text-xs font-semibold text-red-600 mb-1">Fraud Indicators:</p>
                      <ul className="text-xs text-red-600 space-y-1">
                        {msg.fraudIndicators.map((indicator, i) => (
                          <li key={i}>• {indicator}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <Loader className="animate-spin text-primary-600" size={20} />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        <form onSubmit={handleSend} className="mb-6">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your response..."
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="bg-primary-600 text-white px-6 py-3 rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Send size={20} />
            </button>
          </div>
        </form>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}

        {questionCount < 3 && !autoAnalyzing && (
          <button
            onClick={handleContinue}
            className="w-full bg-gray-200 text-gray-800 py-3 px-6 rounded-lg font-medium hover:bg-gray-300 transition-colors flex items-center justify-center gap-2"
          >
            Skip Remaining Questions & Analyze Now
            <ArrowRight size={20} />
          </button>
        )}
        {autoAnalyzing && (
          <div className="w-full bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-2"></div>
            <p className="text-blue-800 text-sm">Analyzing fraud risk...</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default AIQuestioning

