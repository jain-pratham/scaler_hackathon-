'use client';

import styles from './TicketSummary.module.css';

export default function TicketSummary({
  ticket = null,
  environmentState = null,
  onViewMetrics,
}) {
  if (!ticket) {
    return (
      <div className={styles.summaryCard}>
        <h2 className={styles.sectionTitle}>Customer Support Ticket</h2>
        <p className={styles.emptyState}>Select a ticket to view its details.</p>
      </div>
    );
  }

  const policyRules = environmentState?.policy_rules ?? [];
  const progress = environmentState?.progress ?? {};

  return (
    <div className={styles.summaryCard}>
      <h2 className={styles.sectionTitle}>Customer Support Ticket</h2>

      <div className={styles.summaryBody}>
        <div className={styles.summaryItem}>
          <span className={styles.label}>Ticket ID</span>
          <span className={styles.valueMono}>{ticket.id}</span>
        </div>
        <div className={styles.summaryItem}>
          <span className={styles.label}>Category</span>
          <span className={styles.value}>{ticket.category}</span>
        </div>
        <div className={styles.summaryItem}>
          <span className={styles.label}>Customer</span>
          <span className={styles.value}>{ticket.customer}</span>
        </div>
        <div className={styles.summaryItem}>
          <span className={styles.label}>Order</span>
          <span className={styles.value}>{ticket.orderId}</span>
        </div>
        <div className={styles.summaryItem}>
          <span className={styles.label}>Product</span>
          <span className={styles.value}>{ticket.product}</span>
        </div>
        <div className={styles.summaryItem}>
          <span className={styles.label}>Order Date</span>
          <span className={styles.value}>{ticket.orderDateText}</span>
        </div>
        <div className={`${styles.summaryItem} ${styles.fullWidth}`}>
          <span className={styles.label}>Issue</span>
          <div className={styles.issueBox}>{ticket.issue}</div>
        </div>
        <div className={styles.summaryItem}>
          <span className={styles.label}>Status</span>
          <span className={styles.statusBadge}>{ticket.status}</span>
        </div>
        <div className={styles.summaryItem}>
          <span className={styles.label}>Classification</span>
          <span className={styles.value}>{progress.classification ?? 'pending'}</span>
        </div>
        <div className={styles.summaryItem}>
          <span className={styles.label}>Reply</span>
          <span className={styles.value}>{progress.reply ?? 'pending'}</span>
        </div>
        <div className={styles.summaryItem}>
          <span className={styles.label}>Escalation</span>
          <span className={styles.value}>{progress.escalation ?? 'not_needed'}</span>
        </div>

        <div className={`${styles.summaryItem} ${styles.fullWidth}`}>
          <span className={styles.label}>Policy</span>
          <div className={styles.policyList}>
            {policyRules.length ? (
              policyRules.map((rule) => <p key={rule}>{rule}</p>)
            ) : (
              <p>Policy details load after reset.</p>
            )}
          </div>
        </div>
      </div>

      <button className={styles.metricsButton} onClick={onViewMetrics}>
        View Performance
      </button>
    </div>
  );
}
