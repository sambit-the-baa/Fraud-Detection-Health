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
  const messagesEndRef = useRef(null)

  useEffect(() => {
    // Initial AI greeting
    setMessages([{
      type: 'ai',
      content: 'Hello! I\'m here to help process your claim. I\'ll ask you some questions about the incident to ensure we have all the necessary information. Please provide as much detail as possible.'
    }])
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return

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

      setMessages(prev => [...prev, {
        type: 'ai',
        content: response.data.ai_message,
        followUpQuestions: response.data.follow_up_questions,
        fraudIndicators: response.data.fraud_indicators
      }])
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send message. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleContinue = async () => {
    // Trigger fraud analysis before navigating
    try {
      await client.post(`/api/claims/${claimId}/analyze-fraud`)
    } catch (err) {
      console.error('Error analyzing fraud:', err)
    }
    navigate(`/claim/${claimId}/analysis`)
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

        <p className="text-gray-600 mb-6">
          Our AI will ask you questions about your claim to help identify any potential issues and ensure accuracy.
        </p>

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

        <button
          onClick={handleContinue}
          className="w-full bg-primary-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-primary-700 transition-colors flex items-center justify-center gap-2"
        >
          Complete Review & Analyze Fraud Risk
          <ArrowRight size={20} />
        </button>
      </div>
    </div>
  )
}

export default AIQuestioning

