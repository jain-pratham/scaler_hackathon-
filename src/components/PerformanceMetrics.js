'use client';

import styles from './PerformanceMetrics.module.css';

function getIndicatorClass(status) {
  if (status === 'correct' || status === 'completed' || status === 'not_needed') {
    return styles.checkIcon;
  }
  if (status === 'required' || status === 'pending') {
    return styles.warningIcon;
  }
  return styles.errorIcon;
}

function getIndicatorLabel(status) {
  if (status === 'correct' || status === 'completed' || status === 'not_needed') {
    return 'OK';
  }
  if (status === 'required' || status === 'pending') {
    return '!';
  }
  return 'X';
}

export default function PerformanceMetrics({
  ticket = null,
  environmentState = null,
  lastReward = 0,
  busyAction = null,
  variant = 'sidebar',
}) {
  if (!ticket) {
    return (
      <div className={styles.metricsContainer}>
        <h2 className={styles.sectionTitle}>Performance</h2>
        <p className={styles.empty}>Select a ticket to see metrics</p>
      </div>
    );
  }

  const progress = environmentState?.progress ?? {
    classification: 'pending',
    reply: 'pending',
    escalation: 'not_needed',
  };
  const policyRules = environmentState?.policy_rules ?? [];
  const rewardScore = Number(environmentState?.reward_score ?? 0.5).toFixed(2);

  return (
    <div
      className={`${styles.metricsContainer} ${
        variant === 'modal' ? styles.metricsContainerModal : ''
      }`}
    >
      <h2 className={styles.sectionTitle}>Performance Metrics</h2>

      <div className={styles.scoreCard}>
        <label>Reward Score</label>
        <div className={styles.scoreValue}>{rewardScore}</div>
        <p className={styles.scoreDelta}>Last reward: {lastReward.toFixed(2)}</p>
      </div>

      <div className={styles.checklistSection}>
        <h3>Progress</h3>
        <div className={styles.checklistItem}>
          <span className={getIndicatorClass(progress.classification)}>
            {getIndicatorLabel(progress.classification)}
          </span>
          <span>Correct Classification</span>
        </div>
        <div className={styles.checklistItem}>
          <span className={getIndicatorClass(progress.reply)}>
            {getIndicatorLabel(progress.reply)}
          </span>
          <span>Pending Reply</span>
        </div>
        <div className={styles.checklistItem}>
          <span className={getIndicatorClass(progress.escalation)}>
            {getIndicatorLabel(progress.escalation)}
          </span>
          <span>Escalation Needed</span>
        </div>
      </div>

      <div className={styles.policySection}>
        <h3>Policy Info</h3>
        {policyRules.length ? (
          policyRules.map((rule) => <p key={rule}>{rule}</p>)
        ) : (
          <p>Policy details load after the environment reset.</p>
        )}
        <p className={styles.policyStatus}>
          Status: {environmentState?.status ?? ticket.status}
        </p>
        <p className={styles.policyMeta}>
          Busy action: {busyAction ?? 'idle'}
        </p>
      </div>
    </div>
  );
}
