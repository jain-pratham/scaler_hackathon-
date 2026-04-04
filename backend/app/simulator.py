from __future__ import annotations

from typing import Any, Optional


class CustomerSimulator:
    def next_customer_message(
        self,
        task: dict[str, Any],
        action: str,
        helpful: bool,
        already_replied: bool,
    ) -> Optional[str]:
        simulation = task.get("customer_simulation", {})

        if action == "respond":
            if helpful:
                if already_replied:
                    return simulation.get("after_followup_response")
                return simulation.get("after_good_response")
            return simulation.get("after_bad_response")

        if action == "close_ticket":
            return simulation.get("after_failed_close")

        if action == "escalate":
            return simulation.get("after_escalation")

        return None
