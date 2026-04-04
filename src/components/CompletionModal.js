'use client';

import PerformanceMetrics from './PerformanceMetrics';
import styles from './CompletionModal.module.css';

export default function CompletionModal({
  open,
  ticket,
  environmentState,
  lastReward,
  busyAction,
  onClose,
}) {
  if (!open) return null;

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div
        className={styles.modalCard}
        onClick={(event) => event.stopPropagation()}
      >
        <div className={styles.modalHeader}>
          <div>
            <p className={styles.eyebrow}>Episode Complete</p>
            <h2 className={styles.title}>Performance Metrics</h2>
          </div>
          <button className={styles.iconButton} onClick={onClose} aria-label="Close metrics popup">
            X
          </button>
        </div>

        <div className={styles.modalBody}>
          <PerformanceMetrics
            ticket={ticket}
            environmentState={environmentState}
            lastReward={lastReward}
            busyAction={busyAction}
            variant="modal"
          />
        </div>

        <div className={styles.modalFooter}>
          <button className={styles.closeButton} onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
