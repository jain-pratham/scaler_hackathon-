import 'server-only';

import { promises as fs } from 'node:fs';
import path from 'node:path';

const TASKS_DIR = path.join(process.cwd(), 'tasks');
const DIFFICULTIES = ['easy', 'medium', 'hard'];

async function loadTaskBundle(difficulty) {
  const filePath = path.join(TASKS_DIR, `${difficulty}.json`);
  const raw = await fs.readFile(filePath, 'utf8');
  return JSON.parse(raw);
}

export async function getTicketCatalog() {
  const bundles = await Promise.all(
    DIFFICULTIES.map(async (difficulty) => {
      const parsed = await loadTaskBundle(difficulty);
      return parsed.tasks.map((task) => ({
        id: task.ticket.id,
        category: task.display_category,
        customer: task.ticket.customer,
        issue: task.ticket.issue,
        difficulty,
        status: 'open',
        orderId: task.ticket.order_id,
        product: task.ticket.product,
        orderDateText: task.ticket.order_date_text,
      }));
    }),
  );

  return bundles.flat();
}

export async function getTaskByTicketId(ticketId) {
  for (const difficulty of DIFFICULTIES) {
    const parsed = await loadTaskBundle(difficulty);
    const task = parsed.tasks.find(
      (entry) => entry.ticket.id === ticketId || entry.ticket_id === ticketId,
    );

    if (task) {
      return {
        ...task,
        difficulty,
      };
    }
  }

  return null;
}
