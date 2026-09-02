export default function ResultCard({
  check,
}) {
  const statusClass =
    check.status.toLowerCase();

  const evidence =
    check.evidence;

  return (
    <article className="result-card">
      <div className="result-card-header">
        <div>
          <p className="rule-id">
            {check.rule_id}
          </p>

          <h3>
            {check.label}
          </h3>
        </div>

        <span
          className={`status-badge ${statusClass}`}
        >
          {check.status}
        </span>
      </div>

      {evidence ? (
        <div className="result-details">
          <div className="result-row">
            <span>
              Detected Value
            </span>

            <strong>
              {evidence.normalized_value}
            </strong>
          </div>

          <div className="result-row">
            <span>
              Confidence
            </span>

            <strong>
              {(
                evidence.confidence *
                100
              ).toFixed(1)}
              %
            </strong>
          </div>
        </div>
      ) : (
        <div className="missing-evidence">
          No declaration evidence
          detected.
        </div>
      )}

      <p className="reason">
        {check.reason}
      </p>
    </article>
  );
}