from __future__ import annotations

from typing import Optional

from .models import TaskDefinition


class CustomerSimulator:
    def next_customer_message(
        self,
        task: TaskDefinition,
        action: str,
        helpful: bool,
        already_replied: bool,
    ) -> Optional[str]:
        simulation = task.customer_simulation

        if action == "respond":
            if helpful:
                if already_replied:
                    return simulation.after_followup_response
                return simulation.after_good_response
            return simulation.after_bad_response

        if action == "close_ticket":
            return simulation.after_failed_close

        if action == "escalate":
            return simulation.after_escalation

        return None
