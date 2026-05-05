import React, { useEffect, useMemo, useState } from 'react';
import {
  getItem,
  getMastery,
  getOperatorAttempts,
  getOperatorItem,
  getOperatorItems,
  getOperatorUnmatchedPaths,
  getOperatorWeaknessReport,
  getParentSummary,
  getTodaySession,
  markParentSummarySent,
  submitAttempt,
  submitReflection,
} from './api.js';

const emptyAttempt = {
  finalAnswer: '',
  steps: [''],
};

const emptySessionStats = {
  attempted: 0,
  correct: 0,
  coreCorrect: 0,
  repairAttempts: 0,
  hintsUsed: 0,
};

export default function App() {
  const viewMode = new URLSearchParams(window.location.search).get('view');
  return viewMode === 'operator' ? <OperatorDashboard /> : <StudentApp />;
}

function StudentApp() {
  const [session, setSession] = useState(null);
  const [activeTask, setActiveTask] = useState(null);
  const [item, setItem] = useState(null);
  const [attempt, setAttempt] = useState(emptyAttempt);
  const [outcome, setOutcome] = useState(null);
  const [mastery, setMastery] = useState([]);
  const [hintLevel, setHintLevel] = useState(0);
  const [repairContext, setRepairContext] = useState(null);
  const [sessionStats, setSessionStats] = useState(emptySessionStats);
  const [screen, setScreen] = useState('work');
  const [reflectionTarget, setReflectionTarget] = useState(null);
  const [reflectionText, setReflectionText] = useState('');
  const [articulationOk, setArticulationOk] = useState(false);
  const [status, setStatus] = useState('Loading today\'s session.');
  const [error, setError] = useState('');

  useEffect(() => {
    loadSession();
  }, []);

  async function loadSession() {
    setError('');
    setScreen('work');
    try {
      const [sessionData, masteryData] = await Promise.all([
        getTodaySession(),
        getMastery(),
      ]);
      setSession(sessionData);
      setMastery(masteryData.vectors);
      setStatus('Ready.');
    } catch (err) {
      setError(err.message);
      setStatus('API unavailable. Start the backend server, then refresh.');
    }
  }

  async function openTask(task, context = null) {
    if (task.locked) return;
    setError('');
    setOutcome(null);
    setScreen('work');
    setRepairContext(context);
    setHintLevel(0);
    setAttempt(emptyAttempt);
    try {
      const itemData = await getItem(task.item_id);
      setItem(itemData);
      setActiveTask(task);
      setStatus(`${task.track.toUpperCase()} selected.`);
    } catch (err) {
      setError(err.message);
    }
  }

  async function checkAnswer() {
    if (!item || !activeTask) return;
    setError('');
    try {
      const payload = {
        item_id: item.id,
        track: activeTask.track,
        submitted_answer: attempt.finalAnswer,
        submitted_steps: attempt.steps.filter((step) => step.trim()),
        hint_level_used: hintLevel,
        repair_context: activeTask.track === 'repair' ? repairContext : null,
      };
      const result = await submitAttempt(payload);
      setOutcome(result);
      const [masteryData, sessionData] = await Promise.all([getMastery(), getTodaySession()]);
      setMastery(masteryData.vectors);
      setSession(sessionData);
      const nextStats = {
        attempted: sessionStats.attempted + 1,
        correct: sessionStats.correct + (result.correct ? 1 : 0),
        coreCorrect: sessionStats.coreCorrect + (result.correct && activeTask.track === 'core' ? 1 : 0),
        repairAttempts: sessionStats.repairAttempts + (activeTask.track === 'repair' ? 1 : 0),
        hintsUsed: sessionStats.hintsUsed + (hintLevel > 0 ? 1 : 0),
      };
      setSessionStats(nextStats);
      if (result.correct && activeTask.track === 'core' && nextStats.coreCorrect >= 3) {
        setReflectionTarget(item);
        setStatus('Core complete. Capture the thinking link before ending.');
      } else if (result.correct && activeTask.track === 'repair') {
        setStatus('Repair link restored. Return to the original problem.');
      } else {
        setStatus(result.correct ? 'Answer checked. Ready for the next step.' : 'Stuck point detected.');
      }
    } catch (err) {
      setError(err.message);
    }
  }

  async function storeReflection() {
    if (!reflectionTarget) return;
    setError('');
    try {
      await submitReflection({
        item_id: reflectionTarget.id,
        reflection_text: reflectionText,
        articulation_ok: articulationOk,
      });
      const masteryData = await getMastery();
      setMastery(masteryData.vectors);
      setScreen('summary');
      setStatus('Session complete.');
    } catch (err) {
      setError(err.message);
    }
  }

  function finishWithReflection() {
    if (reflectionTarget) {
      setScreen('reflection');
      setStatus('Write one sentence about the thinking move that became clearer.');
    }
  }

  function resetLocalSession() {
    setItem(null);
    setActiveTask(null);
    setOutcome(null);
    setAttempt(emptyAttempt);
    setHintLevel(0);
    setRepairContext(null);
    setSessionStats(emptySessionStats);
    setReflectionTarget(null);
    setReflectionText('');
    setArticulationOk(false);
    setScreen('work');
    loadSession();
  }

  async function openNextFromOutcome() {
    if (!outcome) return;
    if (outcome.correct && activeTask?.track !== 'repair') {
      setItem(null);
      setActiveTask(null);
      setOutcome(null);
      setAttempt(emptyAttempt);
      setHintLevel(0);
      setRepairContext(null);
      setStatus('Session plan updated.');
      return;
    }
    const nextTask = {
      track: outcome.next_track,
      item_id: outcome.next_item_id,
      item_title: outcome.next_item_id,
      reason: outcome.next_track === 'repair' ? 'targeted repair' : 'return to learning path',
      locked: false,
    };
    await openTask(nextTask, outcome.repair_context_after);
  }

  const visibleHint = useMemo(() => {
    if (!item || hintLevel === 0) return null;
    return item.hint_ladder.find((hint) => hint.level === hintLevel);
  }, [item, hintLevel]);

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">SUMIN STUDY</p>
          <h1>Today&apos;s maths session</h1>
        </div>
        <button className="ghost-button" onClick={loadSession}>Refresh</button>
      </header>

      {error && <div className="notice error">{error}</div>}
      <div className="notice">{status}</div>

      <section className="workspace">
        <aside className="task-list" aria-label="Today's tasks">
          <h2>Session Plan</h2>
          <div className="session-progress">
            <strong>{sessionStats.coreCorrect} / 3 Core links</strong>
            <span>{sessionStats.correct} correct from {sessionStats.attempted} attempts</span>
          </div>
          {session?.tasks?.map((task) => {
            const repairFromCurrentOutcome =
              task.track === 'repair'
              && outcome?.next_track === 'repair'
              && outcome?.next_item_id === task.item_id
              && outcome?.repair_context_after;
            const repairNeedsContext = task.track === 'repair' && !repairFromCurrentOutcome;
            return (
              <button
                className={`task-row ${activeTask?.item_id === task.item_id ? 'active' : ''}`}
                key={`${task.track}-${task.item_id}`}
                onClick={() => openTask(task, repairFromCurrentOutcome || null)}
                disabled={task.locked || repairNeedsContext}
              >
                <span>{task.track}</span>
                <strong>{task.item_title}</strong>
                <small>
                  {task.locked
                    ? 'Complete Core first'
                    : repairNeedsContext ? 'Open from feedback after Core' : task.reason}
                </small>
              </button>
            );
          })}
        </aside>

        <section className="problem-panel" aria-label="Problem workspace">
          {screen === 'reflection' && (
            <div className="reflection-panel">
              <span className="panel-kicker">Reflection</span>
              <h2>Name the thinking link</h2>
              <p>
                Write one sentence about what became clearer. Keep it specific to the method,
                the sign choice, or the form of the answer.
              </p>
              <textarea
                value={reflectionText}
                onChange={(event) => setReflectionText(event.target.value)}
                placeholder="Example: I need the two bracket numbers to match both the product and the sum."
              />
              <label className="check-row">
                <input
                  type="checkbox"
                  checked={articulationOk}
                  onChange={(event) => setArticulationOk(event.target.checked)}
                />
                <span>I named the method and why it fits.</span>
              </label>
              <div className="action-row">
                <button className="primary-button" onClick={storeReflection}>Save reflection</button>
                <button className="ghost-button" onClick={() => setScreen('summary')}>Skip for today</button>
              </div>
            </div>
          )}

          {screen === 'summary' && (
            <div className="summary-panel">
              <span className="panel-kicker">Session End</span>
              <h2>Today&apos;s work is saved</h2>
              <div className="session-metrics">
                <div><strong>{sessionStats.coreCorrect}</strong><span>Core links</span></div>
                <div><strong>{sessionStats.repairAttempts}</strong><span>Repair attempts</span></div>
                <div><strong>{sessionStats.hintsUsed}</strong><span>Hint-supported items</span></div>
              </div>
              <p>
                The useful signal from today is where the method connected, where repair helped,
                and which idea is ready to revisit next time.
              </p>
              <button className="primary-button" onClick={resetLocalSession}>Start another session</button>
            </div>
          )}

          {screen === 'work' && !item && (
            <div className="empty-state">
              <h2>Choose today&apos;s Core task</h2>
              <p>The session starts with Core, then Review and Explore become useful after the first attempt.</p>
            </div>
          )}

          {screen === 'work' && item && (
            <>
              <div className="problem-header">
                <span>{activeTask.track}</span>
                <h2>{item.title}</h2>
              </div>
              {activeTask.track === 'repair' && (
                <div className="repair-banner">
                  <strong>Repair link</strong>
                  <span>This short problem rebuilds the step needed for the original question.</span>
                </div>
              )}
              <p className="prompt">{item.problem_text}</p>
              <p className="student-prompt">{item.student_prompt}</p>

              {item.metacognition_prompt && (
                <label className="field-label">
                  Before you start
                  <input placeholder={item.metacognition_prompt} />
                </label>
              )}

              <div className="steps">
                <div className="steps-title">
                  <h3>Your work</h3>
                  <button
                    className="ghost-button"
                    onClick={() => setAttempt((current) => ({ ...current, steps: [...current.steps, ''] }))}
                  >
                    Add step
                  </button>
                </div>
                {attempt.steps.map((step, index) => (
                  <input
                    key={index}
                    value={step}
                    placeholder={`Step ${index + 1}`}
                    onChange={(event) => {
                      const nextSteps = [...attempt.steps];
                      nextSteps[index] = event.target.value;
                      setAttempt((current) => ({ ...current, steps: nextSteps }));
                    }}
                  />
                ))}
              </div>

              <label className="field-label">
                Final answer
                <input
                  value={attempt.finalAnswer}
                  onChange={(event) => setAttempt((current) => ({ ...current, finalAnswer: event.target.value }))}
                  placeholder="Type your answer"
                />
              </label>

              <div className="action-row">
                <button className="primary-button" onClick={checkAnswer}>Check answer</button>
                <button
                  className="ghost-button"
                  onClick={() => setHintLevel((level) => Math.min(level + 1, item.hint_ladder.length))}
                >
                  Hint {hintLevel > 0 ? `L${hintLevel}` : ''}
                </button>
              </div>

              {visibleHint && (
                <aside className="hint-panel">
                  <span>Hint {visibleHint.level} of {item.hint_ladder.length}</span>
                  <h3>{visibleHint.title}</h3>
                  <p>{visibleHint.prompt}</p>
                </aside>
              )}
            </>
          )}
        </section>

        <aside className="feedback-panel" aria-label="Feedback and progress">
          <h2>Feedback</h2>
          {screen === 'reflection' && <p>Save one reflection to update the articulation signal.</p>}
          {screen === 'summary' && <p>Session saved. Start another session when ready.</p>}
          {screen === 'work' && !outcome && <p>Check an answer to see the next step.</p>}
          {screen === 'work' && outcome && (
            <div className="outcome">
              <strong>{outcome.correct ? 'Correct' : 'Needs repair'}</strong>
              <p>{outcome.feedback}</p>
              {outcome.stuck_point && <p>{outcome.stuck_point.diagnostic_sentence}</p>}
              {!outcome.correct && outcome.step_checks?.length > 0 && (
                <div className="step-checks">
                  {outcome.step_checks.map((check) => (
                    <div key={`${check.submitted_index}-${check.expected_step_number ?? 'x'}`}>
                      <span>{check.status}</span>
                      <p>{check.diagnostic_sentence ?? check.submitted_text}</p>
                    </div>
                  ))}
                </div>
              )}
              <button className="primary-button" onClick={openNextFromOutcome}>
                {outcome.correct && activeTask?.track !== 'repair'
                  ? 'Back to Session Plan'
                  : outcome.next_track === 'repair' ? 'Go to Repair' : 'Return to original problem'}
              </button>
              {reflectionTarget && screen === 'work' && (
                <button className="ghost-button wide-button" onClick={finishWithReflection}>
                  Finish session
                </button>
              )}
            </div>
          )}

          <h2>Mastery</h2>
          <div className="mastery-list">
            {mastery.length === 0 && <p>No mastery evidence yet.</p>}
            {mastery.map((vector) => (
              <div className="mastery-row" key={vector.concept_id}>
                <strong>{vector.concept_name_en}</strong>
                <span>Accuracy: {vector.accuracy}</span>
                <span>Hint independence: {vector.hint_independence}</span>
                <span>Articulation: {vector.articulation}</span>
              </div>
            ))}
          </div>

        </aside>
      </section>
    </main>
  );
}

function OperatorDashboard() {
  const [items, setItems] = useState([]);
  const [attempts, setAttempts] = useState([]);
  const [weakness, setWeakness] = useState(null);
  const [unmatched, setUnmatched] = useState([]);
  const [parentSummary, setParentSummary] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);
  const [status, setStatus] = useState('Loading operator view.');
  const [error, setError] = useState('');

  useEffect(() => {
    loadOperatorData();
  }, []);

  async function loadOperatorData() {
    setError('');
    try {
      const [itemsData, attemptsData, weaknessData, unmatchedData, parentData] = await Promise.all([
        getOperatorItems(),
        getOperatorAttempts(),
        getOperatorWeaknessReport(),
        getOperatorUnmatchedPaths(),
        getParentSummary(),
      ]);
      setItems(itemsData.items);
      setAttempts(attemptsData.attempts);
      setWeakness(weaknessData);
      setUnmatched(unmatchedData.unmatched);
      setParentSummary(parentData);
      setStatus('Operator data loaded.');
    } catch (err) {
      setError(err.message);
      setStatus('Operator API unavailable. Start the backend server, then refresh.');
    }
  }

  async function openItem(itemId) {
    setError('');
    try {
      const itemData = await getOperatorItem(itemId);
      setSelectedItem(itemData);
    } catch (err) {
      setError(err.message);
    }
  }

  async function markParentDraftSent() {
    if (!parentSummary || parentSummary.draft_status === 'sent') return;
    setError('');
    try {
      const sentView = await markParentSummarySent();
      setParentSummary((current) => (
        current
          ? {
              ...current,
              draft_status: sentView.draft_status,
              sent_at: sentView.sent_at,
            }
          : current
      ));
      setStatus('Parent draft marked as reviewed locally.');
    } catch (err) {
      setError(err.message);
    }
  }

  const sortedItems = [...items].sort((a, b) => {
    if (a.tier !== b.tier) return a.tier === 'extended' ? -1 : 1;
    return a.id.localeCompare(b.id);
  });
  const activeCount = items.filter((item) => item.status === 'active').length;
  const higherCount = items.filter((item) => item.tier === 'extended').length;
  const repairCount = items.filter((item) => item.tier === 'core_repair').length;
  const gateIssues = items.filter((item) => Object.values(item.gates).some((value) => value !== 'ok'));

  return (
    <main className="app-shell operator-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">SUMIN STUDY / OPERATOR</p>
          <h1>Diagnostic quality console</h1>
        </div>
        <div className="topbar-actions">
          <a className="ghost-link" href="/">Student view</a>
          <button className="ghost-button" onClick={loadOperatorData}>Refresh</button>
        </div>
      </header>

      {error && <div className="notice error">{error}</div>}
      <div className="notice">{status}</div>

      <section className="operator-grid">
        <section className="operator-panel">
          <span className="panel-kicker">Bank Health</span>
          <h2>Item bank</h2>
          <div className="operator-metrics">
            <div><strong>{activeCount}</strong><span>Active items</span></div>
            <div><strong>{higherCount}</strong><span>Higher target</span></div>
            <div><strong>{repairCount}</strong><span>Repair items</span></div>
            <div><strong>{gateIssues.length}</strong><span>Gate issues</span></div>
          </div>
          <div className="operator-table">
            {sortedItems.slice(0, 12).map((item) => (
              <button className="operator-row" key={item.id} onClick={() => openItem(item.id)}>
                <strong>{item.id}</strong>
                <span>{item.title}</span>
                <small>{item.tier === 'extended' ? '4MA1 Higher target' : 'Prerequisite repair'}</small>
              </button>
            ))}
          </div>
        </section>

        <section className="operator-panel">
          <span className="panel-kicker">Diagnosis</span>
          <h2>Weakness report</h2>
          {!weakness && <p>No report loaded.</p>}
          {weakness && (
            <div className="operator-stack">
              <p>{weakness.stuck_point_sentence}</p>
              <div className="summary-line">
                <span>Attempts window</span>
                <strong>{weakness.correct_count} correct / {weakness.attempts_count} attempts</strong>
              </div>
              <div className="summary-line">
                <span>Top error category</span>
                <strong>{weakness.top_error_category ?? 'Not enough evidence'}</strong>
              </div>
              <div className="summary-line">
                <span>Operator support action</span>
                <strong>{weakness.support_action_operator}</strong>
              </div>
            </div>
          )}
        </section>

        <section className="operator-panel">
          <span className="panel-kicker">Attempts</span>
          <h2>Recent attempts</h2>
          <div className="operator-table">
            {attempts.slice(-8).reverse().map((attempt) => (
              <div className="operator-row static-row" key={attempt.id}>
                <strong>{attempt.item_id}</strong>
                <span>{attempt.correct ? 'Correct' : 'Repair signal'} - {attempt.track}</span>
                <small>{attempt.diagnostic_target ?? attempt.path_match_status}</small>
              </div>
            ))}
            {attempts.length === 0 && <p>No attempts yet.</p>}
          </div>
        </section>

        <section className="operator-panel">
          <span className="panel-kicker">Alternative Path Queue</span>
          <h2>Unmatched paths</h2>
          {unmatched.length === 0 && <p>No unmatched successful paths waiting for review.</p>}
          {unmatched.map((path) => (
            <div className="operator-card" key={path.attempt_id}>
              <strong>{path.item_id} - {path.item_title}</strong>
              <ul>
                {path.submitted_steps.map((step, index) => (
                  <li key={`${path.attempt_id}-${index}`}>{step}</li>
                ))}
              </ul>
            </div>
          ))}
        </section>

        <section className="operator-panel">
          <span className="panel-kicker">Parent Draft</span>
          <h2>Weekly support summary</h2>
          {!parentSummary && <p>No parent summary loaded.</p>}
          {parentSummary && (
            <div className="operator-stack">
              <div className="summary-line">
                <span>Improving</span>
                <strong>{parentSummary.improving}</strong>
              </div>
              <div className="summary-line">
                <span>Building next</span>
                <strong>{parentSummary.still_developing}</strong>
              </div>
              <div className="summary-line">
                <span>One thing that would help</span>
                <strong>{parentSummary.one_thing_that_would_help}</strong>
              </div>
              <div className="summary-line">
                <span>Draft status</span>
                <strong>
                  {parentSummary.draft_status}
                  {parentSummary.sent_at ? ` (${new Date(parentSummary.sent_at).toLocaleString()})` : ''}
                </strong>
              </div>
              <button
                className="ghost-button fit-button"
                onClick={markParentDraftSent}
                disabled={parentSummary.draft_status === 'sent'}
              >
                {parentSummary.draft_status === 'sent' ? 'Reviewed locally' : 'Mark reviewed'}
              </button>
            </div>
          )}
        </section>

        <section className="operator-panel">
          <span className="panel-kicker">Selected Item</span>
          <h2>{selectedItem ? selectedItem.id : 'Open an item'}</h2>
          {!selectedItem && <p>Select an item from the bank list to inspect its diagnostic contract.</p>}
          {selectedItem && (
            <div className="operator-stack">
              <p>{selectedItem.title}</p>
              <div className="summary-line">
                <span>Edexcel refs</span>
                <strong>{selectedItem.syllabus_refs.join(', ')}</strong>
              </div>
              <div className="summary-line">
                <span>Sequence band</span>
                <strong>{selectedItem.year10_sequence_band}</strong>
              </div>
              <div className="summary-line">
                <span>Expected answer</span>
                <strong>{selectedItem.expected_answer}</strong>
              </div>
              <div className="operator-card">
                <strong>Diagnostic mappings</strong>
                {selectedItem.error_category_mapping.map((mapping) => (
                  <p key={mapping.code}>{mapping.code}: {mapping.diagnostic_target}</p>
                ))}
              </div>
            </div>
          )}
        </section>
      </section>
    </main>
  );
}
