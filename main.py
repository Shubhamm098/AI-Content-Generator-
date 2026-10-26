from dotenv import load_dotenv

load_dotenv()

import argparse
import json
import uuid
from pathlib import Path

from langgraph.types import Command

from graph.build import build_graph

LAST_THREAD_FILE = Path(".last_thread")


def ask_and_resume(app, config, payload):
    print("\n=== HUMAN REVIEW ===")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    answer = input("\nApprove? (y/n): ").strip().lower()
    status = "APPROVED" if answer in {"y", "yes"} else "REJECTED"
    return app.invoke(Command(resume={"status": status}), config)


def finish(app, config, result):
    # Keep going while the graph pauses at the human gate.
    while "__interrupt__" in result:
        payload = result["__interrupt__"][0].value
        result = ask_and_resume(app, config, payload)

    print("\n=== EXECUTION LOG ===")
    for line in result["execution_log"]:
        print(line)
    print("\nFinal approval status:", result["human_approval"])


def start_new(app):
    thread_id = str(uuid.uuid4())
    LAST_THREAD_FILE.write_text(thread_id)
    config = {"configurable": {"thread_id": thread_id}}
    print(f"Thread id: {thread_id}  (resume later with: python main.py --resume)")

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
    finish(app, config, result)


def resume(app, thread_id):
    config = {"configurable": {"thread_id": thread_id}}
    snap = app.get_state(config)
    if not snap.values:
        print(f"No saved run found for thread {thread_id}.")
        return
    if not snap.next:
        print("That run already finished. Final log:")
        for line in snap.values.get("execution_log", []):
            print(line)
        return
    payload = snap.tasks[0].interrupts[0].value  # the pending review card
    result = ask_and_resume(app, config, payload)
    finish(app, config, result)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", nargs="?", const="LAST", metavar="THREAD_ID",
                        help="resume a paused run (no id = the most recent run)")
    args = parser.parse_args()

    app = build_graph()
    if args.resume is None:
        start_new(app)
    else:
        thread_id = LAST_THREAD_FILE.read_text().strip() if args.resume == "LAST" and LAST_THREAD_FILE.exists() else args.resume
        if thread_id == "LAST":
            print("No previous run found. Start one with: python main.py")
            return
        resume(app, thread_id)


if __name__ == "__main__":
    main()