import Dashboard from '@/components/Dashboard';
import { getTicketCatalog } from '@/lib/taskCatalog';

export default async function Home() {
  const initialTickets = await getTicketCatalog();

  return <Dashboard initialTickets={initialTickets} />;
}
