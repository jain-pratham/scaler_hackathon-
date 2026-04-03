'use client';

import { useMemo, useState } from 'react';
import StageProgressBar from './StageProgressBar';
import FilterButtons from './FilterButtons';
import TicketList from './TicketList';
import TicketDetail from './TicketDetail';
import PerformanceMetrics from './PerformanceMetrics';
import { tickets } from '@/data/tickets';
import styles from './Dashboard.module.css';

export default function Dashboard() {
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [selectedTicketId, setSelectedTicketId] = useState(tickets[0]?.id ?? null);
  const [currentStage] = useState(0);

  const filteredTickets = useMemo(() => {
    if (selectedFilter === 'all') return tickets;
    return tickets.filter((ticket) => ticket.difficulty === selectedFilter);
  }, [selectedFilter]);

  const selectedTicket = useMemo(() => {
    const inFilteredList = filteredTickets.find((ticket) => ticket.id === selectedTicketId);
    if (inFilteredList) return inFilteredList;
    return filteredTickets[0] ?? null;
  }, [filteredTickets, selectedTicketId]);

  const handleFilterChange = (nextFilter) => {
    setSelectedFilter(nextFilter);

    const nextTickets =
      nextFilter === 'all'
        ? tickets
        : tickets.filter((ticket) => ticket.difficulty === nextFilter);

    setSelectedTicketId(nextTickets[0]?.id ?? null);
  };

  return (
    <div className={styles.dashboardContainer}>
      <div className={styles.contentGrid}>
        <aside className={styles.sidebar}>
          <FilterButtons
            selectedFilter={selectedFilter}
            onFilterChange={handleFilterChange}
          />
          <TicketList
            tickets={filteredTickets}
            selectedTicketId={selectedTicket?.id}
            onSelectTicket={setSelectedTicketId}
          />
        </aside>

        <section className={styles.stagePanel}>
          <StageProgressBar currentStage={currentStage} />
        </section>

        <main className={styles.mainContent}>
          <TicketDetail ticket={selectedTicket} />
        </main>

        <aside className={styles.rightSidebar}>
          <PerformanceMetrics ticket={selectedTicket} />
        </aside>
      </div>
    </div>
  );
}
