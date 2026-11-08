import { useState } from 'react'
import { api } from '../api'

function InboxEmailView({ email, onCreated }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleProcess() {
    setLoading(true)
    setError(null)
    try {
      const newCase = await api.processInboxEmail(email.name)
      onCreated(newCase)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="card">
      <h2>{email.subject}</h2>
      <p className="muted">From: {email.sender || 'Unknown sender'}</p>
      <pre className="pre">{email.text}</pre>

      {error && <div className="alert error">{error}</div>}

      <div className="actions top-space">
        <button className="button primary" onClick={handleProcess} disabled={loading}>
          {loading ? 'Agent is working...' : 'Process with agent'}
        </button>
      </div>
    </section>
  )
}

export default InboxEmailView