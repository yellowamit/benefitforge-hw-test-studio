import React, { useState, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function App() {
  const [participants, setParticipants] = useState([])
  const [plans, setPlans] = useState([])
  const [preflight, setPreflight] = useState(null)
  const [testReport, setTestReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [qleDiff, setQleDiff] = useState(null)
  const [qleError, setQleError] = useState(null)
  const [qleSuccessMsg, setQleSuccessMsg] = useState(null)

  const [qleForm, setQleForm] = useState({
    participant_id: 1,
    plan_id: 1,
    qle_type: 'BIRTH',
    event_date: '2026-05-10',
    submitted_date: '2026-05-20',
    target_coverage_tier: 'EE_FAMILY',
    annual_hsa_contribution: 6500,
    include_dependent_ids: [1, 2]
  })

  const fetchParticipants = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/participants`)
      const data = await res.json()
      setParticipants(data.participants || [])
      setPlans(data.plans || [])
    } catch (e) {
      console.error('Failed to load participants:', e)
    }
  }

  const fetchReports = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/sandbox/reports`)
      setTestReport(await res.json())
    } catch (e) {
      console.error('Failed to load reports:', e)
    }
  }

  useEffect(() => {
    fetchParticipants()
    fetchReports()
  }, [])

  // Auto-sync dependent selection when participant changes
  const handleParticipantChange = (newPartId) => {
    const pId = Number(newPartId)
    const selectedPart = participants.find((p) => p.id === pId)
    const defaultDepIds = selectedPart ? selectedPart.dependents.map((d) => d.id) : []
    setQleForm((prev) => ({
      ...prev,
      participant_id: pId,
      include_dependent_ids: defaultDepIds
    }))
    setQleDiff(null)
    setQleError(null)
    setQleSuccessMsg(null)
  }

  const handleSeed = async (scenario) => {
    setLoading(true)
    setQleDiff(null)
    setQleError(null)
    setQleSuccessMsg(null)
    try {
      await fetch(`${API_BASE}/api/sandbox/seed`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario })
      })
      await fetchParticipants()
    } catch (e) {
      console.error('Seed error:', e)
    } finally {
      setLoading(false)
    }
  }

  const handlePreflight = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/sandbox/preflight`, { method: 'POST' })
      setPreflight(await res.json())
    } catch (e) {
      console.error('Preflight error:', e)
    } finally {
      setLoading(false)
    }
  }

  const handleRunTests = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/sandbox/run-tests`, { method: 'POST' })
      setTestReport(await res.json())
      await fetchParticipants()
    } catch (e) {
      console.error('Run tests error:', e)
    } finally {
      setLoading(false)
    }
  }

  const toggleDependentId = (id) => {
    setQleForm((prev) => {
      const exists = prev.include_dependent_ids.includes(id)
      const newIds = exists
        ? prev.include_dependent_ids.filter((dId) => dId !== id)
        : [...prev.include_dependent_ids, id]
      return { ...prev, include_dependent_ids: newIds }
    })
  }

  const handleSimulateQle = async (e) => {
    e.preventDefault()
    setLoading(true)
    setQleDiff(null)
    setQleError(null)
    setQleSuccessMsg(null)

    try {
      const res = await fetch(`${API_BASE}/api/enrollments/process-qle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...qleForm,
          participant_id: Number(qleForm.participant_id),
          plan_id: Number(qleForm.plan_id),
          annual_hsa_contribution: Number(qleForm.annual_hsa_contribution || 0),
          include_dependent_ids: qleForm.include_dependent_ids
        })
      })
      const data = await res.json()
      if (!res.ok) {
        setQleError(data.detail || 'QLE Processing Failed.')
      } else {
        setQleDiff(data)
        setQleSuccessMsg(data.message)
        await fetchParticipants()
      }
    } catch (err) {
      setQleError(err.message || 'Network error executing QLE.')
    } finally {
      setLoading(false)
    }
  }

  const downloadFile = (content, filename, mime) => {
    if (!content) return
    const blob = new Blob([content], { type: mime })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = filename
    a.click()
  }

  const currentParticipant = participants.find((p) => p.id === Number(qleForm.participant_id))
  const selectedPlan = plans.find((pl) => pl.id === Number(qleForm.plan_id))

  const calculateAge = (dobStr, refDateStr) => {
    if (!dobStr) return null
    const dob = new Date(dobStr)
    const ref = refDateStr ? new Date(refDateStr) : new Date()
    let age = ref.getFullYear() - dob.getFullYear()
    const m = ref.getMonth() - dob.getMonth()
    if (m < 0 || (m === 0 && ref.getDate() < dob.getDate())) {
      age--
    }
    return age
  }

  return (
    <div>
      <header className="studio-header">
        <div>
          <h1>BenefitForge — Health & Welfare (HW) QA & Test Studio</h1>
          <p>HIPAA-Safe Seeding | Pre-Flight Compliance Diagnostics | Deterministic QLE Simulation | Prescribed Verification</p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <span className="header-badge">{loading ? 'PROCESSING...' : 'SANDBOX ACTIVE'}</span>
        </div>
      </header>

      <main className="container">
        {/* Section 1 & 2: Data Setup and Diagnostics */}
        <div className="grid-2">
          <section className="card">
            <h2>
              <span>1. Test Data Setup: HIPAA-Safe Cohorts</span>
            </h2>
            <div className="btn-group">
              <button onClick={() => handleSeed('all')} disabled={loading}>Seed All Cohorts</button>
              <button className="secondary" onClick={() => handleSeed('open_enrollment')} disabled={loading}>Open Enrollment</button>
              <button className="secondary" onClick={() => handleSeed('qle_life_events')} disabled={loading}>QLE Life Events</button>
              <button className="secondary" onClick={() => handleSeed('dependent_age_out')} disabled={loading}>Age-26 Boundary</button>
            </div>
            <table>
              <thead>
                <tr>
                  <th>Code / Name</th>
                  <th>Status</th>
                  <th>Dependents</th>
                  <th>Active Tier</th>
                  <th>Paycheck Ded.</th>
                </tr>
              </thead>
              <tbody>
                {participants.map((p) => (
                  <tr
                    key={p.id}
                    className={`selectable ${Number(qleForm.participant_id) === p.id ? 'selected-row' : ''}`}
                    onClick={() => handleParticipantChange(p.id)}
                    title="Click to load participant into QLE Simulator"
                  >
                    <td>
                      <strong>{p.employee_code}</strong>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{p.full_name}</div>
                    </td>
                    <td>
                      <span className={`badge ${p.employment_status}`}>{p.employment_status}</span>
                    </td>
                    <td>
                      {p.dependents.length === 0 ? (
                        <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>None</span>
                      ) : (
                        p.dependents.map((d) => {
                          const age = calculateAge(d.dob, '2026-06-01')
                          const isAgedOut = d.relationship_type === 'CHILD' && age >= 26 && !d.is_disabled
                          return (
                            <span key={d.id} className={`dep-pill ${isAgedOut ? 'aged-out' : ''}`}>
                              {d.full_name.split(' ')[0]} ({d.relationship_type.charAt(0)}{age !== null ? `, ${age}y` : ''})
                            </span>
                          )
                        })
                      )}
                    </td>
                    <td>
                      <span className="badge tier-badge">
                        {p.active_election ? p.active_election.coverage_tier : 'NONE'}
                      </span>
                    </td>
                    <td>
                      {p.active_election ? `$${Number(p.active_election.per_paycheck_deduction).toFixed(2)}` : '$0.00'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="card">
            <h2>
              <span>2. Environment Setup: Pre-Flight DB Checks</span>
              <button onClick={handlePreflight} disabled={loading}>Run DB Diagnostics</button>
            </h2>
            {!preflight ? (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                Click <strong>Run DB Diagnostics</strong> to execute schema, constraint, and referential integrity checks against PostgreSQL.
              </p>
            ) : (
              <>
                <div className="metrics-summary">
                  <div className="metric-pill">
                    <div className="metric-val">
                      <span className={`badge ${preflight.overall_status}`}>{preflight.overall_status}</span>
                    </div>
                    <div className="metric-label">Status</div>
                  </div>
                  <div className="metric-pill">
                    <div className="metric-val">{preflight.duration_ms} ms</div>
                    <div className="metric-label">Diagnostic Latency</div>
                  </div>
                  <div className="metric-pill">
                    <div className="metric-val">
                      {preflight.checks.filter((c) => c.status === 'PASSED').length}/{preflight.checks.length}
                    </div>
                    <div className="metric-label">Checks Passed</div>
                  </div>
                </div>
                <table>
                  <thead>
                    <tr>
                      <th>Compliance Check</th>
                      <th>Status</th>
                      <th>Verification Detail</th>
                    </tr>
                  </thead>
                  <tbody>
                    {preflight.checks.map((c, i) => (
                      <tr key={i}>
                        <td><strong>{c.check_name}</strong></td>
                        <td><span className={`badge ${c.status}`}>{c.status}</span></td>
                        <td>{c.detail}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            )}
          </section>
        </div>

        {/* Section 3 & 4: Simulator & Test Execution */}
        <div className="grid-2">
          <section className="card">
            <h2>3. Live QLE Simulator & Atomic DB State Diff Viewer</h2>
            <form onSubmit={handleSimulateQle}>
              <div className="form-row">
                <div>
                  <label>Participant Target</label>
                  <select
                    value={qleForm.participant_id}
                    onChange={(e) => handleParticipantChange(e.target.value)}
                  >
                    {participants.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.employee_code} — {p.full_name} ({p.employment_status})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label>Benefit Plan Target</label>
                  <select
                    value={qleForm.plan_id}
                    onChange={(e) => setQleForm({ ...qleForm, plan_id: Number(e.target.value) })}
                  >
                    {plans.map((pl) => (
                      <option key={pl.id} value={pl.id}>
                        {pl.plan_code} ({pl.hsa_eligible ? 'HSA Eligible' : 'Non-HSA PPO'})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div>
                  <label>Life Event (QLE)</label>
                  <select
                    value={qleForm.qle_type}
                    onChange={(e) => setQleForm({ ...qleForm, qle_type: e.target.value })}
                  >
                    <option value="BIRTH">BIRTH (30d statutory window)</option>
                    <option value="MARRIAGE">MARRIAGE (30d statutory window)</option>
                    <option value="LOSS_OF_COVERAGE">LOSS_OF_COVERAGE (30d statutory window)</option>
                    <option value="OPEN_ENROLLMENT">OPEN_ENROLLMENT (No 30d window limit)</option>
                  </select>
                </div>
                <div>
                  <label>Target Coverage Tier</label>
                  <select
                    value={qleForm.target_coverage_tier}
                    onChange={(e) => setQleForm({ ...qleForm, target_coverage_tier: e.target.value })}
                  >
                    <option value="EE_ONLY">EE_ONLY (Employee Only)</option>
                    <option value="EE_SPOUSE">EE_SPOUSE (Employee + Spouse)</option>
                    <option value="EE_CHILD">EE_CHILD (Employee + Child)</option>
                    <option value="EE_FAMILY">EE_FAMILY (Employee + Family)</option>
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div>
                  <label>QLE Event Date</label>
                  <input
                    type="date"
                    value={qleForm.event_date}
                    onChange={(e) => setQleForm({ ...qleForm, event_date: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label>Submission Date</label>
                  <input
                    type="date"
                    value={qleForm.submitted_date}
                    onChange={(e) => setQleForm({ ...qleForm, submitted_date: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="form-row">
                <div>
                  <label>
                    Annual HSA Contribution ($)
                    <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginLeft: '0.4rem' }}>
                      (Max: {qleForm.target_coverage_tier === 'EE_ONLY' ? '$4,300.00' : '$8,550.00'})
                    </span>
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="8550"
                    value={qleForm.annual_hsa_contribution}
                    onChange={(e) => setQleForm({ ...qleForm, annual_hsa_contribution: e.target.value })}
                  />
                </div>
                <div>
                  <label>Selected Medical Plan Details</label>
                  <div style={{ padding: '0.42rem 0.6rem', background: '#f5f7f6', borderRadius: '5px', fontSize: '0.78rem' }}>
                    {selectedPlan ? (
                      <span>
                        Base EE: <strong>${selectedPlan.base_monthly_ee.toFixed(2)}/mo</strong> | HSA:{' '}
                        <strong>{selectedPlan.hsa_eligible ? 'Eligible' : 'Ineligible'}</strong>
                      </span>
                    ) : 'None selected'}
                  </div>
                </div>
              </div>

              {/* Dependents Checkbox Group */}
              {currentParticipant && currentParticipant.dependents.length > 0 && (
                <div>
                  <label>Include Dependents in Coverage:</label>
                  <div className="dependents-checkbox-group">
                    {currentParticipant.dependents.map((dep) => {
                      const ageOnEvent = calculateAge(dep.dob, qleForm.event_date)
                      const isAge26Out = dep.relationship_type === 'CHILD' && ageOnEvent >= 26 && !dep.is_disabled
                      const isChecked = qleForm.include_dependent_ids.includes(dep.id)
                      return (
                        <label key={dep.id} className="dependent-checkbox-label">
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={() => toggleDependentId(dep.id)}
                          />
                          <span>
                            <strong>{dep.full_name}</strong> ({dep.relationship_type}, DOB: {dep.dob}, Age on Event: {ageOnEvent})
                            {isAge26Out && (
                              <span className="badge FAILED" style={{ marginLeft: '0.5rem' }}>
                                AGE &gt;= 26 (Boundary Violation)
                              </span>
                            )}
                          </span>
                        </label>
                      )
                    })}
                  </div>
                </div>
              )}

              <button type="submit" disabled={loading}>
                {loading ? 'Processing...' : 'Execute QLE & Assert Atomic DB Mutation'}
              </button>
            </form>

            {qleError && (
              <div className="alert-box error">
                <strong>ATOMIC ROLLBACK EXECUTED:</strong> {qleError}
              </div>
            )}

            {qleSuccessMsg && (
              <div className="alert-box success">
                <strong>TRANSACTION COMMITTED:</strong> {qleSuccessMsg}
              </div>
            )}

            {qleDiff && (
              <div className="diff-box">
                <div className="diff-col">
                  <h4>Before DB State</h4>
                  <div className="diff-row">
                    <span>Coverage Tier:</span>
                    <strong>{qleDiff.before_state.coverage_tier || 'NONE'}</strong>
                  </div>
                  <div className="diff-row">
                    <span>Paycheck Deduction:</span>
                    <strong>
                      {qleDiff.before_state.per_paycheck_deduction != null
                        ? `$${Number(qleDiff.before_state.per_paycheck_deduction).toFixed(2)}`
                        : '$0.00'}
                    </strong>
                  </div>
                  <div className="diff-row">
                    <span>Annual HSA:</span>
                    <strong>
                      ${Number(qleDiff.before_state.annual_hsa_contribution || 0).toFixed(2)}
                    </strong>
                  </div>
                  <div className="diff-row">
                    <span>Effective Date:</span>
                    <span>{qleDiff.before_state.effective_date || 'N/A'}</span>
                  </div>
                  <div className="diff-row">
                    <span>Status:</span>
                    <span className={`badge ${qleDiff.before_state.status}`}>
                      {qleDiff.before_state.status}
                    </span>
                  </div>
                </div>

                <div className="diff-col">
                  <h4>After DB State (Atomically Applied)</h4>
                  <div className="diff-row">
                    <span>Coverage Tier:</span>
                    <strong style={{ color: 'var(--sage-hover)' }}>
                      {qleDiff.after_state.coverage_tier}
                    </strong>
                  </div>
                  <div className="diff-row">
                    <span>Paycheck Deduction:</span>
                    <strong style={{ color: 'var(--sage-hover)' }}>
                      ${Number(qleDiff.after_state.per_paycheck_deduction).toFixed(2)}
                    </strong>
                  </div>
                  <div className="diff-row">
                    <span>Annual HSA:</span>
                    <strong>
                      ${Number(qleDiff.after_state.annual_hsa_contribution || 0).toFixed(2)}
                    </strong>
                  </div>
                  <div className="diff-row">
                    <span>Effective Date:</span>
                    <span>{qleDiff.after_state.effective_date}</span>
                  </div>
                  <div className="diff-row">
                    <span>Status:</span>
                    <span className={`badge ${qleDiff.after_state.status}`}>
                      {qleDiff.after_state.status}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </section>

          <section className="card">
            <h2>
              <span>4. Automated Test Execution & Result Matrix</span>
              <button onClick={handleRunTests} disabled={loading}>
                {loading ? 'Running Tests...' : 'Run Full Pytest Suite'}
              </button>
            </h2>

            {testReport && testReport.results && testReport.results.length > 0 ? (
              <>
                <div className="metrics-summary">
                  <div className="metric-pill">
                    <div className="metric-val">{testReport.results.length}</div>
                    <div className="metric-label">Total Tests</div>
                  </div>
                  <div className="metric-pill">
                    <div className="metric-val" style={{ color: '#2d6a4f' }}>
                      {testReport.results.filter((r) => r.status === 'PASSED').length}
                    </div>
                    <div className="metric-label">Passed</div>
                  </div>
                  <div className="metric-pill">
                    <div className="metric-val" style={{ color: '#9b2226' }}>
                      {testReport.results.filter((r) => r.status === 'FAILED').length}
                    </div>
                    <div className="metric-label">Failed</div>
                  </div>
                </div>

                <div className="btn-group">
                  <button
                    className="secondary"
                    onClick={() => downloadFile(testReport.markdown, 'hw_verification_matrix.md', 'text/markdown')}
                  >
                    Download Matrix (.md)
                  </button>
                  <button
                    className="secondary"
                    onClick={() => downloadFile(testReport.csv, 'hw_verification_matrix.csv', 'text/csv')}
                  >
                    Download Matrix (.csv)
                  </button>
                  <button
                    className="secondary"
                    onClick={() => downloadFile(JSON.stringify(testReport.results, null, 2), 'hw_verification_matrix.json', 'application/json')}
                  >
                    Download Matrix (.json)
                  </button>
                </div>

                <table>
                  <thead>
                    <tr>
                      <th>Req ID</th>
                      <th>Persona / Rule</th>
                      <th>Suite</th>
                      <th>Test Case</th>
                      <th>Status</th>
                      <th>Latency</th>
                    </tr>
                  </thead>
                  <tbody>
                    {testReport.results.map((r, i) => (
                      <tr key={i}>
                        <td><strong>{r.requirement_id}</strong></td>
                        <td>{r.persona}</td>
                        <td>
                          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>{r.suite}</span>
                        </td>
                        <td style={{ fontFamily: 'monospace', fontSize: '0.74rem' }}>{r.test_case}</td>
                        <td><span className={`badge ${r.status}`}>{r.status}</span></td>
                        <td>{r.duration_ms} ms</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            ) : (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                Click <strong>Run Full Pytest Suite</strong> to execute the full unit and database-backed integration test suite and generate verification reports.
              </p>
            )}
          </section>
        </div>
      </main>
    </div>
  )
}
