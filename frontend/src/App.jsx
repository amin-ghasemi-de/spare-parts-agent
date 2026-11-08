import { useEffect, useState } from 'react'
import { api } from './api'
import CaseList from './components/CaseList'
import CaseView from './components/CaseView'
import NewRequest from './components/NewRequest'

function App() {
  const [cases, setCases] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    api
      .getCases()
      .then(setCases)
      .catch((err) => setError(err.message))
  }, [])

  function handleCaseCreated(newCase) {
    setCases((current) => [newCase, ...current])
    setSelectedId(newCase.id)
  }

  function handleCaseUpdated(updatedCase) {
    setCases((current) =>
      current.map((caseItem) => (caseItem.id === updatedCase.id ? updatedCase : caseItem)),
    )
  }

  const selectedCase = cases.find((caseItem) => caseItem.id === selectedId)

  return (
    <div className="layout">
      <aside className="sidebar">
        <h1 className="logo">Spare-Parts Agent</h1>
        <button className="button primary full" onClick={() => setSelectedId(null)}>
          + New request
        </button>
        <CaseList cases={cases} selectedId={selectedId} onSelect={setSelectedId} />
      </aside>

      <main className="content">
        {error && <div className="alert error">{error}</div>}
        {selectedCase ? (
          <CaseView key={selectedCase.id} caseData={selectedCase} onUpdated={handleCaseUpdated} />
        ) : (
          <NewRequest onCreated={handleCaseCreated} />
        )}
      </main>
    </div>
  )
}

export default App