function CaseView({ caseData }) {
  return (
    <section className="card">
      <h2>Case {caseData.id}</h2>
      <pre className="pre">{caseData.result.draft || '(no draft)'}</pre>
    </section>
  )
}

export default CaseView