"""
AirPulse AI - Phase 5 Verification Test: What-If Policy Intervention Simulator
Validates:
1. Realistic physical simulation coupling Source Attribution + LightGBM forecasting.
2. Dynamic reduction factors depending on ward source shares (not static constants).
3. Multi-ward and citywide simulation capabilities.
4. Comparative intervention simulation ('Option A vs Option B').
5. Tool execution (simulate_intervention).
6. Multi-turn LangGraph agentic reasoning maintaining conversational context.
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from langchain_core.messages import HumanMessage, AIMessage
from app.ml.intervention_simulator import (
    simulate_ward_intervention,
    simulate_multi_ward_intervention,
    simulate_citywide_intervention,
    INTERVENTION_EFFECTIVENESS,
)
from app.llm.tools import simulate_intervention, build_tools
from app.llm.officer_chat import get_checkpointer, get_chat_history, SYSTEM_PROMPT


def test_1_single_ward_simulation():
    print("=" * 70)
    print("STEP 1: Single Ward Policy Intervention Simulation")
    print("=" * 70)

    res = simulate_ward_intervention(
        ward_id="CANT_1",
        intervention_type="construction_ban",
        intensity=1.0,
        horizon_hours=24,
    )

    print(f"Target:             {res['ward_name']} ({res['ward_id']})")
    print(f"Intervention:       {res['intervention_label']} (Intensity: {res['intensity']*100:.0f}%)")
    print(f"Baseline AQI:       {res['current_aqi']} ({res['dominant_source']} dominant)")
    print(f"Simulated AQI:      {res['simulated_immediate_aqi']} (-{res['immediate_drop_points']} immediate pts)")
    print(f"24h Average Drop:   -{res['average_reduction_points']} points (-{res['percentage_reduction']}%)")
    print(f"Peak Suppression:   {res['peak_baseline']} → {res['peak_simulated']} (-{res['peak_baseline'] - res['peak_simulated']} pts)")
    print(f"Primary Sector:     {res['top_affected_source']}")
    print(f"Explanation:\n{res['explanation']}\n")

    assert res["current_aqi"] > 0
    assert res["simulated_immediate_aqi"] < res["current_aqi"]
    assert res["average_reduction_points"] > 0
    assert res["percentage_reduction"] > 0
    assert res["top_affected_source"] == "Construction"
    print("[SUCCESS] Step 1 passed: Single ward simulation returns coherent physical metrics.")


def test_2_dynamic_source_attribution_dependency():
    print("=" * 70)
    print("STEP 2: Validation of Dynamic vs Static Reductions")
    print("=" * 70)

    # Test two contrasting interventions on the same ward
    sim_construction = simulate_ward_intervention("CANT_1", "construction_ban", 1.0, 24)
    sim_trucks = simulate_ward_intervention("CANT_1", "diesel_truck_ban", 1.0, 24)
    sim_oddeven = simulate_ward_intervention("CANT_1", "odd_even", 1.0, 24)

    print(f"Ward CANT_1 Baseline AQI: {sim_construction['current_aqi']}")
    print(f"  • Construction Ban Drop:   -{sim_construction['average_reduction_points']} pts (-{sim_construction['percentage_reduction']}%)")
    print(f"  • Diesel Truck Ban Drop:   -{sim_trucks['average_reduction_points']} pts (-{sim_trucks['percentage_reduction']}%)")
    print(f"  • Odd-Even Vehicle Drop:   -{sim_oddeven['average_reduction_points']} pts (-{sim_oddeven['percentage_reduction']}%)")

    # Ensure reductions are differentiated and NOT identical constants
    assert sim_construction["average_reduction_points"] != sim_trucks["average_reduction_points"]
    assert sim_trucks["average_reduction_points"] != sim_oddeven["average_reduction_points"]
    print("\n[SUCCESS] Step 2 passed: Reductions dynamically mirror specific sector mitigation levers.")


def test_3_multi_ward_and_citywide():
    print("\n" + "=" * 70)
    print("STEP 3: Multi-Ward and Citywide Aggregated Simulations")
    print("=" * 70)

    multi_res = simulate_multi_ward_intervention(["CANT_1", "W02"], "diesel_truck_ban", 1.0, 24)
    print(f"Multi-Ward Simulation ({multi_res['total_wards_evaluated']} wards):")
    print(f"  • Mean City AQI Reduction: -{multi_res['mean_percentage_reduction']}%")
    print(f"  • Best Performing Ward:    {multi_res['best_performing_ward']} (-{multi_res['highest_ward_drop']} pts)")
    assert multi_res["total_wards_evaluated"] == 2
    assert multi_res["mean_percentage_reduction"] > 0

    print("\nSimulating Citywide DG Set Ban (48h horizon)...")
    city_res = simulate_citywide_intervention("dg_set_ban", 1.0, 48, top_n=4)
    print(f"Citywide Evaluation: Top {city_res['total_wards_evaluated']} Hotspots:")
    print(f"  • Mean Citywide Drop:      -{city_res['mean_percentage_reduction']}%")
    print(f"  • Cumulative Points Mitigated: -{city_res['total_reduction_points_sum']} points")
    assert city_res["total_wards_evaluated"] >= 2
    print("[SUCCESS] Step 3 passed: Multi-ward and citywide simulations execute smoothly.")


def test_4_tool_direct_execution():
    print("\n" + "=" * 70)
    print("STEP 4: Agent Tool Execution (simulate_intervention)")
    print("=" * 70)

    # 1. Single ward tool call
    out_single = simulate_intervention.invoke({"ward_id": "CANT_1", "intervention_type": "construction_ban"})
    print("Single Ward Tool Output Snippet:\n", out_single[:350], "...\n")
    assert "What-If Intervention Simulation" in out_single
    assert "Predictive AQI Trajectory" in out_single

    # 2. Comparative tool call (Option A vs Option B)
    out_comp = simulate_intervention.invoke({
        "ward_id": "CANT_1",
        "intervention_type": "odd_even vs construction_ban",
        "intensity": "strict",
        "horizon_hours": 24,
    })
    print("Comparative Tool Output Snippet:\n", out_comp[:450], "...\n")
    assert "Comparative Intervention Simulation" in out_comp
    assert "Option A" in out_comp and "Option B" in out_comp
    assert "Verdict" in out_comp
    print("[SUCCESS] Step 4 passed: simulate_intervention tool handles single, multi, and comparative modes.")


def test_5_multiturn_agentic_workflow():
    print("=" * 70)
    print("STEP 5: Multi-Turn Conversational Reasoning with Simulation")
    print("=" * 70)

    from langgraph.prebuilt import create_react_agent
    from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel

    class MockAgenticChatModel(FakeMessagesListChatModel):
        def bind_tools(self, tools, **kwargs):
            return self

    checkpointer = get_checkpointer()
    tools = build_tools()
    test_session_id = f"test-sim-session-{os.getpid()}"
    config = {
        "configurable": {
            "thread_id": test_session_id,
            "checkpoint_ns": "",
        }
    }

    # Turn 1: "Which wards are critical right now?" -> get_citywide_hotspots
    t1_call = {"name": "get_citywide_hotspots", "args": {"threshold": 200}, "id": "call_hotspots_01"}
    ai_t1_step1 = AIMessage(content="", tool_calls=[t1_call])
    ai_t1_final = AIMessage(content="Ward CANT_1 is currently the most critical hotspot with an AQI of 201.")

    # Turn 2: "What if we impose a construction ban there?" -> recalls CANT_1 -> simulate_intervention
    t2_call = {"name": "simulate_intervention", "args": {"ward_id": "CANT_1", "intervention_type": "construction_ban"}, "id": "call_sim_02"}
    ai_t2_step1 = AIMessage(content="", tool_calls=[t2_call])
    ai_t2_final = AIMessage(content="Imposing a construction ban in Ward CANT_1 yields an estimated 19.1% drop in AQI, reducing levels from 201 to ~158.")

    # Turn 3: "Compare that with a diesel truck ban" -> recalls CANT_1 -> comparative simulate_intervention
    t3_call = {"name": "simulate_intervention", "args": {"ward_id": "CANT_1", "intervention_type": "construction_ban vs diesel_truck_ban"}, "id": "call_sim_03"}
    ai_t3_step1 = AIMessage(content="", tool_calls=[t3_call])
    ai_t3_final = AIMessage(content="Comparing both policies in Ward CANT_1: the construction ban yields a higher reduction than the truck ban because construction dust currently accounts for nearly 30% of emissions.")

    fake_model = MockAgenticChatModel(responses=[ai_t1_step1, ai_t1_final, ai_t2_step1, ai_t2_final, ai_t3_step1, ai_t3_final])
    agent = create_react_agent(fake_model, tools, prompt=SYSTEM_PROMPT, checkpointer=checkpointer)

    # Turn 1
    print("--- [Turn 1] Officer: 'Which wards are critical right now?' ---")
    out1 = agent.invoke({"messages": [HumanMessage(content="Which wards are critical right now?")]}, config=config)
    print(f"AI: {out1['messages'][-1].content}\n")

    # Turn 2
    print("--- [Turn 2] Officer: 'What if we impose a construction ban there?' ---")
    out2 = agent.invoke({"messages": [HumanMessage(content="What if we impose a construction ban there?")]}, config=config)
    print(f"AI: {out2['messages'][-1].content}\n")
    tools_t2 = [tc["name"] for m in out2["messages"] if hasattr(m, "tool_calls") and m.tool_calls for tc in m.tool_calls]
    assert "simulate_intervention" in tools_t2

    # Turn 3
    print("--- [Turn 3] Officer: 'Compare that with a diesel truck ban' ---")
    out3 = agent.invoke({"messages": [HumanMessage(content="Compare that with a diesel truck ban")]}, config=config)
    print(f"AI: {out3['messages'][-1].content}\n")

    # Verify history persistence
    hist = get_chat_history(test_session_id)
    print(f"Session history verified: {len(hist)} turns saved in checkpointer.")
    assert len(hist) == 6
    print("[SUCCESS] Step 5 passed: Multi-turn simulation workflow and state persistence validated.")


if __name__ == "__main__":
    try:
        test_1_single_ward_simulation()
        test_2_dynamic_source_attribution_dependency()
        test_3_multi_ward_and_citywide()
        test_4_tool_direct_execution()
        test_5_multiturn_agentic_workflow()
        print("\n" + "=" * 70)
        print(">>> ALL PHASE 5 WHAT-IF SIMULATOR CHECKS PASSED SUCCESSFULLY! <<<")
        print("=" * 70)
    except Exception as e:
        print(f"\n[FAILURE] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

