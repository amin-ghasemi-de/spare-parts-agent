import { useState } from 'react'
import { api } from '../api'

const STATUS_LABELS = {
  pending_review: 'To review',
  approved: 'Approved',
  rejected: 'Rejected',
}

function formatArguments(args) {
  return Object.entries(args)
    .map(([key, value]) => `${key}=${JSON.stringify(value)}`)
    .join(', ')
}

function CaseView({ caseData, onUpdated }) {
  const { result } = caseData
  const extraction = result.extraction
  const isRequest = result.status !== 'not_a_request'

  const [replyText, setReplyText] = useState(result.draft || '')
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const isPending = caseData.status === 'pending_review'
  const isEdited = replyText.trim() !== (result.draft || '').trim()

  async function decide(action) {
    setBusy(true)
    setError(null)
    try {
      const updated =
        action === 'approve'
          ? await api.approveCase(caseData.id, replyText, note || null)
          : await api.rejectCase(caseData.id, note || null)
      onUpdated(updated)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <div className="case-header">
        <h2>Case {caseData.id}</h2>
        <span className={`badge ${caseData.status}`}>{STATUS_LABELS[caseData.status]}</span>
      </div>

      {result.needs_attention && <div className="alert attention">⚠ {result.attention_reason}</div>}
      {!isRequest && (
        <div className="alert attention">
          This e-mail is not a spare-part request, so the agent was not run. Reject it or forward it
          to the right team.
        </div>
      )}
      {result.status === 'max_steps_reached' && (
        <div className="alert error">
          The agent stopped after the maximum number of steps. Please check this case manually.
        </div>
      )}

      <div className="grid-2">
        <section className="card">
          <h3>Customer e-mail</h3>
          <pre className="pre">{caseData.email_text}</pre>
        </section>

        <section className="card">
          <h3>Extracted data</h3>
          <dl className="fields">
            <dt>Company</dt>
            <dd>{extraction.customer_company || '–'}</dd>
            <dt>Contact</dt>
            <dd>{extraction.contact_name || '–'}</dd>
            <dt>E-mail</dt>
            <dd>{extraction.contact_email || '–'}</dd>
            <dt>Machine model</dt>
            <dd>{extraction.machine_model || '–'}</dd>
            <dt>Urgency</dt>
            <dd>{extraction.urgency}</dd>
            <dt>Language</dt>
            <dd>{extraction.language}</dd>
          </dl>

          {isRequest && (
            <table className="items">
              <thead>
                <tr>
                  <th>Part no. (as written)</th>
                  <th>Description</th>
                  <th>Qty</th>
                </tr>
              </thead>
              <tbody>
                {extraction.items.map((item, index) => (
                  <tr key={index}>
                    <td>{item.part_no || '–'}</td>
                    <td>{item.description}</td>
                    <td>{item.quantity ?? '–'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </div>

      {isRequest && (
        <>
          <section className="card">
            <h3>Agent summary</h3>
            <pre className="pre">{(result.summary || 'No summary.').replaceAll('**', '')}</pre>
          </section>

          <section className="card">
            <h3>
              Tool calls ({result.trace.length}) · {result.steps_used} agent steps
            </h3>
            {result.trace.map((record, index) => (
              <details key={index} className="trace-step">
                <summary>
                  {index + 1}. {record.tool}({formatArguments(record.arguments)})
                </summary>
                <pre className="pre">{JSON.stringify(record.result, null, 2)}</pre>
              </details>
            ))}
          </section>
        </>
      )}

      <section className="card">
        <h3>{isRequest ? 'Reply' : 'Decision'}</h3>
        {isPending ? (
          <>
            {isRequest && (
              <textarea
                className="draft-input"
                rows={16}
                value={replyText}
                onChange={(event) => setReplyText(event.target.value)}
                disabled={busy}
              />
            )}
            {isRequest && isEdited && (
              <p className="muted small">
                You edited the agent draft.{' '}
                <button className="link" onClick={() => setReplyText(result.draft || '')}>
                  Reset to agent draft
                </button>
              </p>
            )}
            {error && <div className="alert error">{error}</div>}
            <div className="actions">
              <input
                className="note-input"
                placeholder="Note for the record (optional)"
                value={note}
                onChange={(event) => setNote(event.target.value)}
                disabled={busy}
              />
              <button className="button danger" onClick={() => decide('reject')} disabled={busy}>
                Reject
              </button>
              {isRequest && (
                <button
                  className="button primary"
                  onClick={() => decide('approve')}
                  disabled={busy || replyText.trim() === ''}
                >
                  Approve &amp; send to outbox
                </button>
              )}
            </div>
          </>
        ) : (
          <>
            {caseData.final_reply && <pre className="pre">{caseData.final_reply}</pre>}
            <p className="muted small">
              {STATUS_LABELS[caseData.status]} at{' '}
              {new Date(caseData.decided_at).toLocaleString('de-DE')}
              {caseData.edited_by_human ? ' · edited by employee' : ''}
              {caseData.reviewer_note ? ` · Note: ${caseData.reviewer_note}` : ''}
              {caseData.sent_at ? ` · sent ${new Date(caseData.sent_at).toLocaleString('de-DE')}` : ''}
            </p>
          </>
        )}
      </section>
    </div>
  )
}

export default CaseView