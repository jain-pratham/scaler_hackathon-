'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import styles from './TicketDetail.module.css';

const CATEGORY_OPTIONS = [
  { value: 'refund', label: 'Refund' },
  { value: 'return', label: 'Return' },
  { value: 'delivery', label: 'Delivery' },
  { value: 'account', label: 'Account' },
  { value: 'technical', label: 'Technical' },
  { value: 'other', label: 'Other' },
];

export default function TicketDetail({
  ticket,
  environmentState,
  busyAction,
  errorMessage,
  autoAgentMode,
  onAutoAgentModeChange,
  onRunAutoAgent,
  onGenerateDraftReply,
  onClassify,
  onSendMessage,
  onEscalate,
  onClose,
}) {
  const [replyText, setReplyText] = useState('');
  const [selectedCategory, setSelectedCategory] = useState(CATEGORY_OPTIONS[0].value);
  const conversationRef = useRef(null);

  const conversationHistory = useMemo(() => {
    if (environmentState?.conversation_history?.length) {
      return environmentState.conversation_history;
    }

    if (!ticket) return [];

    return [{ role: 'customer', message: ticket.issue }];
  }, [environmentState, ticket]);

  useEffect(() => {
    if (!conversationRef.current) return;
    conversationRef.current.scrollTop = conversationRef.current.scrollHeight;
  }, [conversationHistory]);

  if (!ticket) {
    return (
      <div className={styles.emptyState}>
        <p>Select a ticket to open the conversation.</p>
      </div>
    );
  }

  const isBusy = Boolean(busyAction) || Boolean(environmentState?.done);

  return (
    <section className={styles.chatCard}>
      <div className={styles.chatHeader}>
        <div>
          <p className={styles.eyebrow}>Live Workspace</p>
          <h2 className={styles.title}>Agent Conversation</h2>
        </div>
        <div className={styles.toggleRow}>
          <label className={styles.toggleLabel}>
            <input
              type="checkbox"
              checked={autoAgentMode}
              onChange={(event) => onAutoAgentModeChange(event.target.checked)}
            />
            Auto Agent Mode
          </label>
          <button
            className={styles.autoButton}
            disabled={isBusy}
            onClick={onRunAutoAgent}
          >
            Run Auto Agent
          </button>
        </div>
      </div>

      <div className={styles.actionBar}>
        <div className={styles.actionGroup}>
          <select
            className={styles.categorySelect}
            value={selectedCategory}
            onChange={(event) => setSelectedCategory(event.target.value)}
            disabled={isBusy}
          >
            {CATEGORY_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <button
            className={styles.primaryButton}
            disabled={isBusy}
            onClick={() => onClassify(selectedCategory)}
          >
            Classify
          </button>
        </div>

        <div className={styles.actionGroup}>
          <button
            className={styles.secondaryButton}
            disabled={isBusy}
            onClick={onEscalate}
          >
            Escalate
          </button>
          <button
            className={styles.secondaryButton}
            disabled={isBusy}
            onClick={onClose}
          >
            Close Ticket
          </button>
        </div>
      </div>

      {!!environmentState?.info_messages?.length && (
        <div className={styles.feedbackBox}>
          {environmentState.info_messages.map((message) => (
            <p key={message}>{message}</p>
          ))}
        </div>
      )}

      {!!errorMessage && <p className={styles.errorText}>{errorMessage}</p>}

      <div ref={conversationRef} className={styles.conversationBox}>
        {conversationHistory.map((entry, index) => {
          const roleClass =
            entry.role === 'agent'
              ? styles.agentMessage
              : entry.role === 'system'
                ? styles.systemMessage
                : styles.customerMessage;

          return (
            <div key={`${entry.role}-${index}`} className={`${styles.message} ${roleClass}`}>
              <span className={styles.messageBadge}>{entry.role}</span>
              <p>{entry.message}</p>
            </div>
          );
        })}
      </div>

      <div className={styles.inputPanel}>
        <textarea
          className={styles.replyInput}
          placeholder={environmentState?.done ? 'Ticket closed.' : 'Type your reply to the customer...'}
          value={replyText}
          onChange={(event) => setReplyText(event.target.value)}
          disabled={isBusy}
          rows={2}
        />
        <button
          className={styles.draftButton}
          disabled={isBusy}
          onClick={async () => {
            const draftMessage = await onGenerateDraftReply();
            if (draftMessage) {
              setReplyText(draftMessage);
            }
          }}
        >
          {busyAction === 'draft-reply' ? 'Generating...' : 'Generate'}
        </button>
        <button
          className={styles.sendButton}
          disabled={isBusy || !replyText.trim()}
          onClick={() => {
            onSendMessage(replyText.trim());
            setReplyText('');
          }}
        >
          Send
        </button>
      </div>
    </section>
  );
}
