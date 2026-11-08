import { useState } from 'react'
import { api } from '../api'

function NewRequest({ onCreated }) {
  const [emailText, setEmailText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit() {
    setLoading(true)
    setError(null)
    try {
      const newCase = await api.createCase(emailText)
      onCreated(newCase)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="card">
      <h2>Paste a customer e-mail</h2>
      <p className="muted">
        Select an e-mail from the inbox on the left, or paste any e-mail here to test the agent.
      </p>

      <textarea
        className="email-input"
        rows={14}
        value={emailText}
        onChange={(event) => setEmailText(event.target.value)}
        placeholder="Paste a customer e-mail here..."
        disabled={loading}
      />

      {error && <div className="alert error">{error}</div>}

      <button
        className="button primary"
        onClick={handleSubmit}
        disabled={loading || emailText.trim().length < 20}
      >
        {loading ? 'Agent is working...' : 'Process with agent'}
      </button>
    </section>
  )
}

export default NewRequest