'use client';

import styles from './PerformanceMetrics.module.css';

export default function PerformanceMetrics({ ticket = null }) {
  if (!ticket) {
    return (
      <div className={styles.metricsContainer}>
        <h2 className={styles.sectionTitle}>Performance</h2>
        <p className={styles.empty}>Select a ticket to see metrics</p>
      </div>
    );
  }

  return (
    <div className={styles.metricsContainer}>
      <h2 className={styles.sectionTitle}>Performance Metrics</h2>

      <div className={styles.scoreCard}>
        <label>Reward Score:</label>
        <div className={styles.scoreValue}>0.72</div>
      </div>

      <div className={styles.checklistSection}>
        <h3>Progress</h3>
        <div className={styles.checklistItem}>
          <span className={styles.checkIcon}>OK</span>
          <span>Correct Classification</span>
        </div>
        <div className={styles.checklistItem}>
          <span className={styles.warningIcon}>!</span>
          <span>Pending Reply</span>
        </div>
        <div className={styles.checklistItem}>
          <span className={styles.errorIcon}>X</span>
          <span>Escalation Needed</span>
        </div>
      </div>

      <div className={styles.policySection}>
        <h3>Policy Info</h3>
        <p>Refunds within 7 days</p>
        <p className={styles.policyStatus}>Status: In Progress</p>
      </div>
    </div>
  );
}
