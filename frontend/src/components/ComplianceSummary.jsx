import ResultCard from "./ResultCard";

export default function ComplianceSummary({
  result,
}) {
  if (!result) {
    return (
      <div className="summary-placeholder">
        <div>
          <div className="placeholder-icon">
            📋
          </div>

          <p>
            Compliance results will
            appear after analysis.
          </p>
        </div>
      </div>
    );
  }

  const compliant =
    result.overall_status ===
    "COMPLIANT_FOR_PROTOTYPE_RULESET";

  const passCount =
    result.checks.filter(
      (check) =>
        check.status === "PASS"
    ).length;

  const failCount =
    result.checks.filter(
      (check) =>
        check.status === "FAIL"
    ).length;

  const reviewCount =
    result.checks.filter(
      (check) =>
        check.status === "REVIEW"
    ).length;

  return (
    <div className="summary">
      <div
        className={`overall-status ${
          compliant
            ? "compliant"
            : "non-compliant"
        }`}
      >
        <div>
          <p className="overall-label">
            Overall Status
          </p>

          <h2>
            {compliant
              ? "Compliant"
              : "Possible Non-Compliance"}
          </h2>

          <p className="ruleset">
            Ruleset:{" "}
            {result.ruleset_id}
          </p>
        </div>

        <div className="overall-icon">
          {compliant ? "✓" : "!"}
        </div>
      </div>

      <div className="summary-stats">
        <div className="stat-card">
          <span>Passed</span>
          <strong>{passCount}</strong>
        </div>

        <div className="stat-card">
          <span>Failed</span>
          <strong>{failCount}</strong>
        </div>

        <div className="stat-card">
          <span>Review</span>
          <strong>{reviewCount}</strong>
        </div>
      </div>

      <div className="result-list">
        {result.checks.map(
          (check) => (
            <ResultCard
              key={check.rule_id}
              check={check}
            />
          )
        )}
      </div>
    </div>
  );
}