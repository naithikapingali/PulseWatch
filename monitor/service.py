"""Run website health checks and send email alerts on failures."""

from .checker import check_endpoint
from .database import list_endpoints, save_result
from .alerts import send_alert

# Remember which endpoints have already triggered an alert.
_failed_endpoints = set()


def run_checks(db_path=None, timeout=8):
    outcomes = []

    for endpoint in list_endpoints(db_path):
        if not endpoint["enabled"]:
            continue

        result = check_endpoint(endpoint, timeout=timeout)
        save_result(result, db_path)
        outcomes.append(result)

        endpoint_id = endpoint["id"]
        name = endpoint.get("name") or endpoint["url"]
        healthy = result["healthy"]

        if not healthy:
            if endpoint_id not in _failed_endpoints:
                subject = f"PulseWatch ALERT: {name} is DOWN"
                message = (
                    f"PulseWatch detected a website failure.\n\n"
                    f"Website: {name}\n"
                    f"URL: {endpoint['url']}\n"
                    f"Status: DOWN\n"
                    f"HTTP status: {result.get('status')}\n"
                    f"Error: {result.get('error')}\n\n"
                    f"Please check your website."
                )

                if send_alert(subject, message):
                    _failed_endpoints.add(endpoint_id)

        else:
            if endpoint_id in _failed_endpoints:
                if send_alert(
                    f"PulseWatch RECOVERED: {name}",
                    f"Good news! {name} is back online."
                ):
                    _failed_endpoints.remove(endpoint_id)

    return outcomes
