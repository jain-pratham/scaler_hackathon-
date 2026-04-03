'use client';

import styles from './TicketDetail.module.css';

export default function TicketDetail({ ticket }) {
  if (!ticket) {
    return (
      <div className={styles.emptyState}>
        <p>Select a ticket to view details</p>
      </div>
    );
  }

  return (
    <div className={styles.detailContainer}>
      <div className={styles.ticketInfoSection}>
        <h2 className={styles.sectionTitle}>Customer Support Ticket</h2>
        <div className={styles.infoGrid}>
          <div className={styles.infoRow}>
            <label>Ticket ID:</label>
            <span className={styles.ticketId}>{ticket.id}</span>
          </div>
          <div className={styles.infoRow}>
            <label>Category:</label>
            <span>{ticket.category}</span>
          </div>
          <div className={styles.infoRow}>
            <label>Customer:</label>
            <span>{ticket.customer}</span>
          </div>
          <div className={styles.infoRow}>
            <label>Issue:</label>
            <span className={styles.issueText}>{ticket.issue}</span>
          </div>
          <div className={styles.infoRow}>
            <label>Order #:</label>
            <span>{ticket.orderId}</span>
          </div>
          <div className={styles.infoRow}>
            <label>Product:</label>
            <span>{ticket.product}</span>
          </div>
          <div className={styles.infoRow}>
            <label>Order Date:</label>
            <span>{ticket.orderDateText}</span>
          </div>
          <div className={styles.infoRow}>
            <label>Status:</label>
            <span className={styles.statusBadge}>{ticket.status}</span>
          </div>
        </div>
      </div>

      <div className={styles.conversationSection}>
        <h2 className={styles.sectionTitle}>Agent Conversation</h2>
        <div className={styles.conversationBox}>
          <div className={`${styles.message} ${styles.agentMessage}`}>
            <span className={styles.messageBadge}>Agent</span>
            <p>How can I assist you today?</p>
          </div>
          <div className={`${styles.message} ${styles.customerMessage}`}>
            <span className={styles.messageBadge}>Customer</span>
            <p>{ticket.issue}</p>
          </div>
        </div>
        <textarea
          className={styles.replyInput}
          placeholder="Type your reply here..."
        />
      </div>
    </div>
  );
}
