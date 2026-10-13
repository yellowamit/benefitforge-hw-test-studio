import React, { useState, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function App() {
  const [participants, setParticipants] = useState([])
  const [preflight, setPreflight] = useState(null)
  const [testReport, setTestReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [qleDiff, setQleDiff] = useState(null)
  const [qleError, setQleError] = useState(null)

  const [qleForm, setQleForm] = useState({
    participant_id: 1, plan_id: 1, qle_type: 'BIRTH',
    event_date: '2026-05-10', submitted_date: '2026-05-18',
    target_coverage_tier: 'EE_FAMILY', annual_hsa_contribution: 6200
  })

  const fetchParticipants = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/participants`)
      const data = await res.json()
      setParticipants(data.participants || [])
    } catch (e) { console.error(e) }
  }

  const fetchReports = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/sandbox/reports`)
      setTestReport(await res.json())
    } catch (e) { console.error(e) }
  }

  useEffect(() => { fetchParticipants(); fetchReports() }, [])

  const handleSeed = async (scenario) => {
    setLoading(true); setQleDiff(null); setQleError(null)
    await fetch(`${API_BASE}/api/sandbox/seed`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario })
    })
    await fetchParticipants(); setLoading(false)
  }

  const handlePreflight = async () => {
    setLoading(true)
    const res = await fetch(`${API_BASE}/api/sandbox/preflight`, { method: 'POST' })
    setPreflight(await res.json()); setLoading(false)
  }

  const handleRunTests = async () => {
    setLoading(true)
    const res = await fetch(`${API_BASE}/api/sandbox/run-tests`, { method: 'POST' })
    setTestReport(await res.json()); await fetchParticipants(); setLoading(false)
  }

  const handleSimulateQle = async (e) => {
    e.preventDefault(); setQleDiff(null); setQleError(null)
    const res = await fetch(`${API_BASE}/api/enrollments/process-qle`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...qleForm,
        participant_id: Number(qleForm.participant_id),
        plan_id: Number(qleForm.plan_id),
        annual_hsa_contribution: Number(qleForm.annual_hsa_contribution),
        include_dependent_ids: []
      })
    })
    const data = await res.json()
    if (!res.ok) setQleError(data.detail || 'QLE Validation Failed')
    else { setQleDiff(data); await fetchParticipants() }
  }

  const downloadFile = (content, filename, mime) => {
    const blob = new Blob([content], { type: mime })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob); a.download = filename; a.click()
  }

  return (
    <div>
      <header className="studio-header">
        <div>
          <h1>BenefitForge — Health & Welfare (HW) QA & Test Orchestration Studio</h1>
          <p>Test Data & Environment Setup | Pre-Flight DB Checks | Automated Execution & Result Analysis</p>
        </div>
        <span className="badge PASSED">{loading ? 'RUNNING...' : 'SANDBOX READY'}</span>
      </header>
      <main className="container">
        <div className="grid-2">
          <section className="card">
            <h2><span>1. Test Data Setup: HIPAA-Safe Cohort Seeder</span></h2>
            <div className="btn-group">
              <button onClick={() => handleSeed('all')}>Seed All HW Cohorts</button>
              <button className="secondary" onClick={() => handleSeed('open_enrollment')}>Open Enrollment</button>
              <button className="secondary" onClick={() => handleSeed('qle_life_events')}>QLE Life Events</button>
              <button className="secondary" onClick={() => handleSeed('dependent_age_out')}>Age-26 Boundary</button>
            </div>
            <table>
              <thead><tr><th>Code</th><th>Participant</th><th>Status</th><th>Tier</th><th>Paycheck Ded.</th></tr></thead>
              <tbody>
                {participants.map((p) => (
                  <tr key={p.id}>
                    <td><strong>{p.employee_code}</strong></td>
                    <td>{p.full_name}</td>
                    <td><span className={`badge ${p.employment_status}`}>{p.employment_status}</span></td>
                    <td>{p.active_election ? p.active_election.coverage_tier : 'NONE'}</td>
                    <td>{p.active_election ? `$${p.active_election.per_paycheck_deduction.toFixed(2)}` : '$0.00'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="card">
            <h2><span>2. Environment Setup: Pre-Flight DB Checks</span><button onClick={handlePreflight}>Run DB Diagnostics</button></h2>
            {!preflight ? <p>Click Run DB Diagnostics to verify PostgreSQL constraints & schema.</p> : (
              <table>
                <thead><tr><th>Check</th><th>Status</th><th>Detail</th></tr></thead>
                <tbody>
                  {preflight.checks.map((c, i) => (
                    <tr key={i}><td><strong>{c.check_name}</strong></td><td><span className={`badge ${c.status}`}>{c.status}</span></td><td>{c.detail}</td></tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        </div>

        <div className="grid-2">
          <section className="card">
            <h2>3. Live QLE Simulator & DB State Diff Viewer</h2>
            <form onSubmit={handleSimulateQle}>
              <div className="form-row">
                <div>
                  <label>Participant</label>
                  <select value={qleForm.participant_id} onChange={(e) => setQleForm({ ...qleForm, participant_id: e.target.value })}>
                    {participants.map((p) => <option key={p.id} value={p.id}>#{p.id} - {p.full_name}</option>)}
                  </select>
                </div>
                <div>
                  <label>Life Event (QLE)</label>
                  <select value={qleForm.qle_type} onChange={(e) => setQleForm({ ...qleForm, qle_type: e.target.value })}>
                    <option value="BIRTH">BIRTH (30d Window)</option>
                    <option value="MARRIAGE">MARRIAGE (30d Window)</option>
                    <option value="OPEN_ENROLLMENT">OPEN_ENROLLMENT</option>
                  </select>
                </div>
              </div>
              <div className="form-row">
                <div><label>Event Date</label><input type="date" value={qleForm.event_date} onChange={(e) => setQleForm({ ...qleForm, event_date: e.target.value })} /></div>
                <div><label>Submitted Date</label><input type="date" value={qleForm.submitted_date} onChange={(e) => setQleForm({ ...qleForm, submitted_date: e.target.value })} /></div>
              </div>
              <div className="form-row">
                <div>
                  <label>Target Coverage Tier</label>
                  <select value={qleForm.target_coverage_tier} onChange={(e) => setQleForm({ ...qleForm, target_coverage_tier: e.target.value })}>
                    <option value="EE_ONLY">EE_ONLY</option>
                    <option value="EE_SPOUSE">EE_SPOUSE</option>
                    <option value="EE_FAMILY">EE_FAMILY</option>
                  </select>
                </div>
                <div><label>Annual HSA ($)</label><input type="number" value={qleForm.annual_hsa_contribution} onChange={(e) => setQleForm({ ...qleForm, annual_hsa_contribution: e.target.value })} /></div>
              </div>
              <button type="submit">Execute QLE & Assert DB Mutation</button>
            </form>
            {qleError && <div style={{ marginTop: '0.75rem', padding: '0.6rem', background: '#ffe5e5', color: '#9b2226', borderRadius: '6px' }}><strong>Rolled Back:</strong> {qleError}</div>}
            {qleDiff && (
              <div className="diff-box">
                <div><strong>BEFORE DB STATE</strong><div>Tier: {qleDiff.before_state.coverage_tier}</div><div>Ded: ${qleDiff.before_state.per_paycheck_deduction}</div></div>
                <div><strong>AFTER DB STATE</strong><div>Tier: <strong>{qleDiff.after_state.coverage_tier}</strong></div><div>Ded: <strong>${qleDiff.after_state.per_paycheck_deduction}</strong></div></div>
              </div>
            )}
          </section>

          <section className="card">
            <h2><span>4. Test Execution & Prescribed Result Matrix</span><button onClick={handleRunTests}>Run Full Pytest Suite</button></h2>
            {testReport && testReport.results && testReport.results.length > 0 ? (
              <>
                <div className="btn-group">
                  <button className="secondary" onClick={() => downloadFile(testReport.markdown, 'hw_verification_matrix.md', 'text/markdown')}>Download .md</button>
                  <button className="secondary" onClick={() => downloadFile(testReport.csv, 'hw_verification_matrix.csv', 'text/csv')}>Download .csv</button>
                </div>
                <table>
                  <thead><tr><th>Req ID</th><th>Persona</th><th>Test Case</th><th>Status</th><th>ms</th></tr></thead>
                  <tbody>
                    {testReport.results.map((r, i) => (
                      <tr key={i}><td><strong>{r.requirement_id}</strong></td><td>{r.persona}</td><td>{r.test_case}</td><td><span className={`badge ${r.status}`}>{r.status}</span></td><td>{r.duration_ms}</td></tr>
                    ))}
                  </tbody>
                </table>
              </>
            ) : <p>Click Run Full Pytest Suite to execute unit & DB tests.</p>}
          </section>
        </div>
      </main>
    </div>
  )
}
