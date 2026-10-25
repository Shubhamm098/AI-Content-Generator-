from dotenv import load_dotenv

load_dotenv()

import json
import uuid

from langgraph.types import Command

from graph.build import build_graph


def main():
    app = build_graph()
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    initial_state = {
        "raw_trends": [],
        "filtered_trend": {},
        "concept_proposals": [],
        "selected_concept": {},
        "generated_assets": {},
        "compliance_passed": False,
        "human_approval": "PENDING",
        "execution_log": [],
    }

    result = app.invoke(initial_state, config)

    # Graph paused at the human gate: show the card, ask, then resume.
    while "__interrupt__" in result:
        payload = result["__interrupt__"][0].value
        print("\n=== HUMAN REVIEW ===")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        answer = input("\nApprove? (y/n): ").strip().lower()
        status = "APPROVED" if answer in {"y", "yes"} else "REJECTED"
        result = app.invoke(Command(resume={"status": status}), config)

    print("\n=== EXECUTION LOG ===")
    for line in result["execution_log"]:
        print(line)
    print("\nFinal approval status:", result["human_approval"])


if __name__ == "__main__":
    main()