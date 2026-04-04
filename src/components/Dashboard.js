'use client';

import { useEffect, useEffectEvent, useMemo, useRef, useState } from 'react';
import StageProgressBar from './StageProgressBar';
import FilterButtons from './FilterButtons';
import TicketList from './TicketList';
import TicketDetail from './TicketDetail';
import TicketSummary from './TicketSummary';
import CompletionModal from './CompletionModal';
import styles from './Dashboard.module.css';

const SESSION_STORAGE_KEY = 'customer-support-session-id';
const REQUEST_TIMEOUT_MS = 5000;
const CATEGORY_VALUE_BY_LABEL = {
  'Refund Request': 'refund',
  'Return Request': 'return',
  'Delivery Problem': 'delivery',
  'Account Issue': 'account',
  'Technical Support': 'technical',
  Other: 'other',
};
const CLOSE_CONFIRMATION_PATTERNS = [
  'may i close',
  'can i close',
  'shall i close',
  'close this ticket',
  'close the ticket',
  'close this case',
  'close the case',
];

async function fetchWithTimeout(url, options = {}) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    return await fetch(url, {
      ...options,
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timeoutId);
  }
}

async function readJson(response) {
  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(payload.detail ?? 'Request failed.');
  }

  return payload;
}

function getErrorMessage(error) {
  if (error?.name === 'AbortError') {
    return 'The request timed out. Please restart the backend and try again.';
  }
  return error?.message ?? 'Request failed.';
}

function isCloseConfirmationMessage(message) {
  const normalizedMessage = message.trim().toLowerCase();
  return CLOSE_CONFIRMATION_PATTERNS.some((pattern) => normalizedMessage.includes(pattern));
}

export default function Dashboard({ initialTickets = [] }) {
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [selectedTicketId, setSelectedTicketId] = useState(initialTickets[0]?.id ?? null);
  const [sessionId, setSessionId] = useState(null);
  const [environmentState, setEnvironmentState] = useState(null);
  const [busyAction, setBusyAction] = useState(null);
  const [lastReward, setLastReward] = useState(0);
  const [autoAgentMode, setAutoAgentMode] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [isMetricsOpen, setIsMetricsOpen] = useState(false);
  const autoRunKeyRef = useRef(null);
  const completedKeyRef = useRef(null);
  const handleAutoRun = useEffectEvent(() => {
    void runAutoAgent();
  });

  const filteredTickets = useMemo(() => {
    if (selectedFilter === 'all') return initialTickets;
    return initialTickets.filter((ticket) => ticket.difficulty === selectedFilter);
  }, [initialTickets, selectedFilter]);

  const selectedTicket = useMemo(() => {
    const inFilteredList = filteredTickets.find((ticket) => ticket.id === selectedTicketId);
    if (inFilteredList) return inFilteredList;
    return filteredTickets[0] ?? null;
  }, [filteredTickets, selectedTicketId]);

  const queueTickets = useMemo(() => {
    if (!environmentState?.ticket?.id) return filteredTickets;

    return filteredTickets.map((ticket) => {
      if (ticket.id !== environmentState.ticket.id) return ticket;

      return {
        ...ticket,
        category:
          environmentState.ticket.category === 'Pending classification'
            ? ticket.category
            : environmentState.ticket.category,
        status: environmentState.ticket.status ?? ticket.status,
      };
    });
  }, [environmentState, filteredTickets]);

  const activeTicket = environmentState?.ticket
    ? {
        ...selectedTicket,
        ...environmentState.ticket,
      }
    : selectedTicket;

  useEffect(() => {
    if (typeof window === 'undefined') return;

    let storedSessionId = window.localStorage.getItem(SESSION_STORAGE_KEY);
    if (!storedSessionId) {
      storedSessionId = window.crypto.randomUUID();
      window.localStorage.setItem(SESSION_STORAGE_KEY, storedSessionId);
    }

    setSessionId(storedSessionId);
  }, []);

  useEffect(() => {
    if (!selectedTicket && filteredTickets[0]) {
      setSelectedTicketId(filteredTickets[0].id);
    }
  }, [filteredTickets, selectedTicket]);

  useEffect(() => {
    if (!sessionId || !selectedTicket) return;

    let ignore = false;

    async function resetTicket() {
      setBusyAction('reset');
      setErrorMessage('');
      setLastReward(0);
      setIsMetricsOpen(false);
      autoRunKeyRef.current = null;
      completedKeyRef.current = null;

      try {
        const response = await fetchWithTimeout('/api/reset', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Session-Id': sessionId,
          },
          body: JSON.stringify({
            difficulty: selectedTicket.difficulty,
            ticketId: selectedTicket.id,
          }),
        });

        const payload = await readJson(response);
        if (!ignore) {
          setEnvironmentState(payload.state);
        }
      } catch (error) {
        if (!ignore) {
          setErrorMessage(getErrorMessage(error));
          setEnvironmentState(null);
        }
      } finally {
        if (!ignore) {
          setBusyAction(null);
        }
      }
    }

    resetTicket();

    return () => {
      ignore = true;
    };
  }, [selectedTicket, sessionId]);

  useEffect(() => {
    if (!autoAgentMode || !environmentState?.ticket?.id || environmentState.done) return;
    if (environmentState.steps_taken !== 0 || busyAction) return;

    const autoRunKey = `${environmentState.ticket.id}:${environmentState.steps_taken}`;
    if (autoRunKeyRef.current === autoRunKey) return;

    autoRunKeyRef.current = autoRunKey;
    handleAutoRun();
  }, [autoAgentMode, busyAction, environmentState]);

  useEffect(() => {
    if (!environmentState?.done || !environmentState?.ticket?.id) return;

    const completionKey = `${environmentState.ticket.id}:${environmentState.steps_taken}`;
    if (completedKeyRef.current === completionKey) return;

    completedKeyRef.current = completionKey;
    setIsMetricsOpen(true);
  }, [environmentState]);

  async function handleStep(payload, options = {}) {
    if (!sessionId) return null;

    const { manageBusyAction = true } = options;

    if (manageBusyAction) {
      setBusyAction(payload.action);
    }
    setErrorMessage('');

    try {
      const response = await fetchWithTimeout('/api/step', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Id': sessionId,
        },
        body: JSON.stringify(payload),
      });

      const result = await readJson(response);
      const nextState = result.info?.state ?? result.observation ?? environmentState;
      setEnvironmentState(nextState);
      setLastReward(result.reward ?? 0);
      return nextState;
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
      return null;
    } finally {
      if (manageBusyAction) {
        setBusyAction(null);
      }
    }
  }

  async function runAutoAgent() {
    if (!sessionId) return;

    setBusyAction('auto-agent');
    setErrorMessage('');

    try {
      const response = await fetchWithTimeout('/api/auto-agent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Id': sessionId,
        },
        body: JSON.stringify({ maxTurns: 8 }),
      });

      const result = await readJson(response);
      setEnvironmentState(result.state ?? environmentState);
      const trajectory = result.trajectory ?? [];
      const totalReward = trajectory.reduce(
        (sum, step) => sum + (Number(step.reward) || 0),
        0,
      );
      setLastReward(Number(totalReward.toFixed(2)));
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setBusyAction(null);
    }
  }

  async function generateDraftReply() {
    if (!sessionId) return '';

    setBusyAction('draft-reply');
    setErrorMessage('');

    try {
      const response = await fetchWithTimeout('/api/draft-reply', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Id': sessionId,
        },
      });

      const result = await readJson(response);
      return result.message ?? '';
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
      return '';
    } finally {
      setBusyAction(null);
    }
  }

  async function sendMessage(message) {
    const trimmedMessage = message.trim();
    if (!trimmedMessage) return;

    const shouldAutoClose = isCloseConfirmationMessage(trimmedMessage);
    if (!shouldAutoClose) {
      await handleStep({
        action: 'respond',
        message: trimmedMessage,
      });
      return;
    }

    setBusyAction('close_ticket');
    setErrorMessage('');

    try {
      let nextState = environmentState;
      const expectedCategory = CATEGORY_VALUE_BY_LABEL[selectedTicket?.category] ?? null;

      if (nextState?.progress?.classification !== 'correct' && expectedCategory) {
        nextState =
          (await handleStep(
            {
              action: 'classify_ticket',
              category: expectedCategory,
            },
            { manageBusyAction: false },
          )) ?? nextState;
      }

      nextState =
        (await handleStep(
          {
            action: 'respond',
            message: trimmedMessage,
          },
          { manageBusyAction: false },
        )) ?? nextState;

      const readyToClose =
        nextState?.progress?.reply === 'completed'
        && (nextState?.customer_ready_to_close || nextState?.status === 'awaiting_close');

      if (readyToClose) {
        await handleStep(
          {
            action: 'close_ticket',
          },
          { manageBusyAction: false },
        );
      }
    } finally {
      setBusyAction(null);
    }
  }

  function handleFilterChange(nextFilter) {
    setSelectedFilter(nextFilter);

    const nextTickets =
      nextFilter === 'all'
        ? initialTickets
        : initialTickets.filter((ticket) => ticket.difficulty === nextFilter);

    setSelectedTicketId(nextTickets[0]?.id ?? null);
  }

  return (
    <div className={styles.dashboardContainer}>
      <div className={styles.contentGrid}>
        <aside className={styles.sidebar}>
          <FilterButtons
            selectedFilter={selectedFilter}
            onFilterChange={handleFilterChange}
          />
          <TicketList
            tickets={queueTickets}
            selectedTicketId={selectedTicket?.id}
            onSelectTicket={setSelectedTicketId}
          />
        </aside>

        <section className={styles.stagePanel}>
          <StageProgressBar currentStage={environmentState?.current_stage ?? 0} />
        </section>

        <main className={styles.mainContent}>
          <TicketDetail
            key={activeTicket?.id ?? 'empty-ticket'}
            ticket={activeTicket}
            environmentState={environmentState}
            busyAction={busyAction}
            errorMessage={errorMessage}
            autoAgentMode={autoAgentMode}
            onAutoAgentModeChange={setAutoAgentMode}
            onRunAutoAgent={runAutoAgent}
            onGenerateDraftReply={generateDraftReply}
            onClassify={(category) =>
              handleStep({
                action: 'classify_ticket',
                category,
              })
            }
            onSendMessage={sendMessage}
            onEscalate={() =>
              handleStep({
                action: 'escalate',
              })
            }
            onClose={() =>
              handleStep({
                action: 'close_ticket',
              })
            }
          />
        </main>

        <aside className={styles.rightSidebar}>
          <TicketSummary
            ticket={activeTicket}
            environmentState={environmentState}
            onViewMetrics={() => setIsMetricsOpen(true)}
          />
        </aside>
      </div>

      <CompletionModal
        open={isMetricsOpen}
        ticket={activeTicket}
        environmentState={environmentState}
        lastReward={lastReward}
        busyAction={busyAction}
        onClose={() => setIsMetricsOpen(false)}
      />
    </div>
  );
}
