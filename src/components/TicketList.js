'use client';

import styles from './TicketList.module.css';

export default function TicketList({ tickets = [], selectedTicketId, onSelectTicket }) {
  const getDifficultyColor = (difficulty) => {
    const colors = {
      easy: '#27ae60',
      medium: '#f39c12',
      hard: '#e74c3c',
    };
    return colors[difficulty] || '#95a5a6';
  };

  return (
    <div className={styles.ticketListContainer}>
      <h3 className={styles.listTitle}>Ticket Queue</h3>
      <div className={styles.ticketsList}>
        {tickets.length === 0 && (
          <p className={styles.emptyList}>No tickets found for this filter.</p>
        )}

        {tickets.map((ticket) => (
          <div
            key={ticket.id}
            className={`${styles.ticketItem} ${
              selectedTicketId === ticket.id ? styles.selected : ''
            }`}
            onClick={() => onSelectTicket(ticket.id)}
          >
            <div className={styles.ticketHeader}>
              <span className={styles.ticketId}>#{ticket.id}</span>
              <span
                className={styles.difficultyBadge}
                style={{ backgroundColor: getDifficultyColor(ticket.difficulty) }}
              >
                {ticket.difficulty.charAt(0).toUpperCase() + ticket.difficulty.slice(1)}
              </span>
            </div>
            <div className={styles.ticketContent}>
              <p className={styles.ticketCategory}>{ticket.category}</p>
              <p className={styles.ticketCustomer}>Customer: {ticket.customer}</p>
              <p className={styles.ticketIssue}>{ticket.issue}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
