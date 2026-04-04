import { NextResponse } from 'next/server';

import { proxyToBackend } from '@/lib/backendProxy';
import { getTaskByTicketId } from '@/lib/taskCatalog';

export const dynamic = 'force-dynamic';

function buildCloseConfirmationDraft(state) {
  const customerName = state?.ticket?.customer ? state.ticket.customer : 'there';
  return `Hi ${customerName}, I am glad that helped. If everything looks good now, may I close this ticket for you?`;
}

function buildKeywordSentence(task) {
  const keywords = task?.reply_guidance?.positive_keywords ?? [];
  const [first, second, third] = keywords;

  switch (task?.expected_category) {
    case 'refund':
      return 'I am sorry the item arrived damaged, and I can help with the refund process right away.';
    case 'return':
      return 'You are within the 14 days return window, and I will send the prepaid label with the return steps.';
    case 'account':
      return 'I will verify the email on file and send a fresh reset link so you can get back into the account.';
    case 'delivery':
      return 'I am reviewing the delivery issue now, I will track the shipment, and I will share an update as soon as possible.';
    case 'technical':
      return 'Please clear the app cache, then log in again so we can restore the sync correctly.';
    default:
      return [first, second, third].filter(Boolean).join(', ');
  }
}

function buildDraftFromTask(state, task) {
  if (state?.customer_ready_to_close || state?.status === 'awaiting_close') {
    return buildCloseConfirmationDraft(state);
  }

  const customerName = state?.ticket?.customer ? `${state.ticket.customer},` : 'there,';
  const policyRules = Array.isArray(task?.policy_rules) ? task.policy_rules.filter(Boolean) : [];
  const lastCustomerMessage = [...(state?.conversation_history ?? [])]
    .reverse()
    .find((entry) => entry?.role === 'customer')?.message;
  const primaryPolicy = policyRules[0] ?? '';
  const secondaryPolicy = policyRules[1] ?? '';
  const needsEscalation = Boolean(task?.resolution?.needs_escalation);

  let message = `Hi ${customerName} I reviewed your message`;
  if (lastCustomerMessage) {
    message += ` about "${lastCustomerMessage}"`;
  }
  message += '. ';
  message += `${buildKeywordSentence(task)} `;

  if (primaryPolicy) {
    message += `${primaryPolicy} `;
  }
  if (secondaryPolicy) {
    message += `${secondaryPolicy} `;
  }

  if (needsEscalation) {
    message += 'I am also escalating this case to a specialist right away and will keep you updated on the next steps.';
  } else {
    message += 'I will document this case clearly and keep you updated on the next steps.';
  }

  return message.replace(/\s+/g, ' ').trim();
}

function buildGenericDraftFromState(state) {
  if (state?.customer_ready_to_close || state?.status === 'awaiting_close') {
    return buildCloseConfirmationDraft(state);
  }

  const customerName = state?.ticket?.customer ? `${state.ticket.customer},` : 'there,';
  const policyRules = Array.isArray(state?.policy_rules) ? state.policy_rules.filter(Boolean) : [];
  const lastCustomerMessage = [...(state?.conversation_history ?? [])]
    .reverse()
    .find((entry) => entry?.role === 'customer')?.message;

  let message = `Hi ${customerName} I reviewed your message`;
  if (lastCustomerMessage) {
    message += ` about "${lastCustomerMessage}"`;
  }
  message += '. ';
  message += 'I am sorry for the inconvenience and I am reviewing the best next step for your case. ';

  if (policyRules[0]) {
    message += `${policyRules[0]} `;
  }
  if (policyRules[1]) {
    message += `${policyRules[1]} `;
  }

  if (state?.progress?.escalation === 'required') {
    message += 'I am escalating this to a specialist right away and will keep you updated.';
  } else {
    message += 'I will document this properly and share the next steps clearly.';
  }

  return message.replace(/\s+/g, ' ').trim();
}

export async function POST(request) {
  try {
    const sessionId = request.headers.get('x-session-id');
    let payload;

    try {
      payload = await proxyToBackend({
        path: '/agent/draft-reply',
        method: 'POST',
        sessionId,
      });
    } catch (error) {
      if (error.status !== 404) {
        throw error;
      }

      const state = await proxyToBackend({
        path: '/state',
        method: 'GET',
        sessionId,
      });

      if (!state?.ticket) {
        const fallbackError = new Error('No active ticket for this session. Call reset first.');
        fallbackError.status = 400;
        throw fallbackError;
      }

      const task = await getTaskByTicketId(state.ticket.id);
      payload = {
        message: task ? buildDraftFromTask(state, task) : buildGenericDraftFromState(state),
        state,
      };
    }

    return NextResponse.json(payload);
  } catch (error) {
    return NextResponse.json(
      { detail: error.message ?? 'Failed to generate a draft reply.' },
      { status: error.status ?? 500 },
    );
  }
}
