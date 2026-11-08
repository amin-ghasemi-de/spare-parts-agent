import { useEffect, useState } from 'react'
import { api } from './api'
import CaseList from './components/CaseList'
import CaseView from './components/CaseView'
import InboxEmailView from './components/InboxEmailView'
import InboxList from './components/InboxList'
import NewRequest from './components/NewRequest'

function App() {
  const [cases, setCases] = useState([])
  const [inbox, setInbox] = useState([])
  const [selection, setSelection] = useState({ type: 'new' })
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([api.getCases(), api.getInbox()])
      .then(([casesData, inboxData]) => {
        setCases(casesData)
        setInbox(inboxData)
      })
      .catch((err) => setError(err.message))
  }, [])

  function handleCaseCreated(newCase) {
    setCases((current) => [newCase, ...current])
    setInbox((current) => current.filter((email) => email.name !== newCase.source))
    setSelection({ type: 'case', id: newCase.id })
  }

  function handleCaseUpdated(updatedCase) {
    setCases((current) =>
      current.map((caseItem) => (caseItem.id === updatedCase.id ? updatedCase : caseItem)),
    )
  }

  const selectedCase =
    selection.type === 'case' ? cases.find((caseItem) => caseItem.id === selection.id) : null
  const selectedEmail =
    selection.type === 'inbox' ? inbox.find((email) => email.name === selection.name) : null

  let mainView
  if (selectedCase) {
    mainView = (
      <CaseView key={selectedCase.id} caseData={selectedCase} onUpdated={handleCaseUpdated} />
    )
  } else if (selectedEmail) {
    mainView = (
      <InboxEmailView key={selectedEmail.name} email={selectedEmail} onCreated={handleCaseCreated} />
    )
  } else {
    mainView = <NewRequest onCreated={handleCaseCreated} />
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <h1 className="logo">Spare-Parts Agent</h1>
        <button className="button full" onClick={() => setSelection({ type: 'new' })}>
          + Paste e-mail
        </button>

        <h3 className="section-title">Inbox ({inbox.length})</h3>
        <InboxList
          emails={inbox}
          selectedName={selection.type === 'inbox' ? selection.name : null}
          onSelect={(name) => setSelection({ type: 'inbox', name })}
        />

        <h3 className="section-title">Cases ({cases.length})</h3>
        <CaseList
          cases={cases}
          selectedId={selection.type === 'case' ? selection.id : null}
          onSelect={(id) => setSelection({ type: 'case', id })}
        />
      </aside>

      <main className="content">
        {error && <div className="alert error">{error}</div>}
        {mainView}
      </main>
    </div>
  )
}

export default App