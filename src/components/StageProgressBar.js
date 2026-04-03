'use client';

import { stageFlow } from '@/data/tickets';
import styles from './StageProgressBar.module.css';

export default function StageProgressBar({ currentStage = 1 }) {
  return (
    <div className={styles.stageContainer}>
      <div className={styles.stagesWrapper}>
        {stageFlow.map((label, index) => {
          const isActive = index <= currentStage;
          const isConnectorActive = index < currentStage;

          return (
            <div key={label} className={styles.stageGroup}>
              <div className={styles.stageItem}>
                <div className={`${styles.stageCircle} ${isActive ? styles.active : ''}`}>
                  {index + 1}
                </div>
                <p className={`${styles.stageLabel} ${isActive ? styles.activeLabel : ''}`}>
                  {label}
                </p>
              </div>

              {index < stageFlow.length - 1 && (
                <div
                  className={`${styles.connector} ${
                    isConnectorActive ? styles.connectorActive : ''
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
