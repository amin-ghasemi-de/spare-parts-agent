function InboxList({ emails, selectedName, onSelect }) {
  if (emails.length === 0) {
    return <p className="muted small">Inbox is empty.</p>
  }

  return (
    <ul className="case-list">
      {emails.map((email) => (
        <li key={email.name}>
          <button
            className={`case-item ${email.name === selectedName ? 'active' : ''}`}
            onClick={() => onSelect(email.name)}
          >
            <div className="case-title">{email.subject}</div>
            <div className="muted small ellipsis">{email.sender || 'Unknown sender'}</div>
          </button>
        </li>
      ))}
    </ul>
  )
}

export default InboxList