const STATUS_LABELS = {
  pending_review: 'To review',
  approved: 'Approved',
  rejected: 'Rejected',
}

function CaseList({ cases, selectedId, onSelect }) {
  if (cases.length === 0) {
    return <p className="muted small">No cases yet.</p>
  }

  return (
    <ul className="case-list">
      {cases.map((caseItem) => {
        const extraction = caseItem.result.extraction
        const title = extraction.customer_company || extraction.contact_name || 'Unknown sender'

        return (
          <li key={caseItem.id}>
            <button
              className={`case-item ${caseItem.id === selectedId ? 'active' : ''}`}
              onClick={() => onSelect(caseItem.id)}
            >
              <div className="case-item-top">
                <span className="case-title">{title}</span>
                {caseItem.result.needs_attention && <span className="badge attention">!</span>}
              </div>
              <div className="case-item-bottom">
                <span className={`badge ${caseItem.status}`}>{STATUS_LABELS[caseItem.status]}</span>
                <span className="muted small">{new Date(caseItem.created_at).toLocaleString('de-DE')}</span>
              </div>
            </button>
          </li>
        )
      })}
    </ul>
  )
}

export default CaseList