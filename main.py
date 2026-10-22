from graph.build import build_graph


def main():
    app = build_graph()

    initial_state = {
        "raw_trends": [],
        "filtered_trend": {},
        "concept_proposals": [],
        "selected_concept": {},
        "generated_assets": {},
        "compliance_passed": False,
        "human_approval": "PENDING",
        "execution_log": []
    }

    final_state = app.invoke(initial_state)

    print("\n===EXECUTION LOG===")
    for line in final_state["execution_log"]:
        print(line)
    print("\nFinal approval status:", final_state["human_approval"])



if __name__ == "__main__":
    main()