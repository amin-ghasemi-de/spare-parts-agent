import { useEffect, useState } from 'react'
import { api } from '../api'

function NewRequest({ onCreated }) {
  const [samples, setSamples] = useState([])
  const [emailText, setEmailText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.getSampleEmails().then(setSamples).catch((err) => setError(err.message))
  }, [])

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
      <h2>New customer e-mail</h2>
      <p className="muted">
        Pick a sample e-mail or paste your own. The agent extracts the request, searches the
        catalog, checks stock and prepares a draft for human review.
      </p>

      <div className="sample-buttons">
        {samples.map((sample) => (
          <button
            key={sample.name}
            className="button small"
            onClick={() => setEmailText(sample.text)}
            disabled={loading}
          >
            {sample.subject}
          </button>
        ))}
      </div>

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