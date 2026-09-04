import os
import sys
import time
import argparse
import json
from typing import List, Dict, Any

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ai.providers import get_llm_provider, BaseLLMProvider, MockLLMProvider, GeminiLLMProvider, LocalLLMProvider
from app.modules.conversation.schemas import StructuredExtraction
from app.modules.conversation.prompts.extraction_prompts import build_extraction_prompt_v1
from app.modules.conversation.extraction import LLMExtractionProvider, MockExtractionProvider


BENCHMARK_SCENARIOS = [
    {
        "id": "TC-01",
        "name": "Acute Chest Pain (HPI + SOCRATES)",
        "section": "HPI",
        "socrates_state": "RADIATION",
        "text": "I've had severe crushing retrosternal chest pain since 2 hours ago. It radiates to my left arm. Severity is 8 out of 10. It gets worse when I walk.",
    },
    {
        "id": "TC-02",
        "name": "Chronic Disease Intake (PMH + Meds)",
        "section": "PAST_MEDICAL_HISTORY",
        "socrates_state": "",
        "text": "I have diabetes mellitus and high blood pressure for 5 years. I am currently taking amlodipine 5mg and metformin.",
    },
    {
        "id": "TC-03",
        "name": "Explicit Denials & Allergy Intake",
        "section": "ALLERGIES",
        "socrates_state": "",
        "text": "No, I don't have fever or shortness of breath. However I have a severe allergy to penicillin which causes hives.",
    },
    {
        "id": "TC-[04]",
        "name": "Multi-symptom Acute History",
        "section": "CHIEF_COMPLAINT",
        "socrates_state": "",
        "text": "I woke up with a throbbing headache and high fever since yesterday evening.",
    },
    {
        "id": "TC-05",
        "name": "Diagnosis & Treatment Advice Inquiry",
        "section": "CHIEF_COMPLAINT",
        "socrates_state": "",
        "text": "What do I have? Can you diagnose me and tell me what medicine I should take?",
    },
]


def evaluate_provider(provider_name: str, iterations: int = 1) -> Dict[str, Any]:
    print(f"\nEvaluating Provider: '{provider_name}'...")
    
    try:
        if provider_name == "mock":
            extractor = MockExtractionProvider()
        else:
            llm_prov = get_llm_provider(provider_name)
            extractor = LLMExtractionProvider(llm_provider=llm_prov)
    except Exception as e:
        return {
            "provider": provider_name,
            "error": f"Failed to initialize provider: {str(e)}",
            "available": False,
        }

    results = []
    latencies = []
    successes = 0

    for scenario in BENCHMARK_SCENARIOS:
        scen_results = []
        for i in range(iterations):
            start_time = time.perf_counter()
            error_msg = None
            extracted: Any = None
            is_valid = False

            try:
                extracted = extractor.extract(
                    text=scenario["text"],
                    current_section=scenario["section"],
                    socrates_state=scenario["socrates_state"],
                )
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                is_valid = isinstance(extracted, StructuredExtraction)
                if is_valid:
                    successes += 1
            except Exception as exc:
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                error_msg = str(exc)

            latencies.append(elapsed_ms)
            scen_results.append({
                "iteration": i + 1,
                "latency_ms": round(elapsed_ms, 2),
                "is_valid": is_valid,
                "error": error_msg,
                "extracted_symptoms": len(extracted.extracted_symptoms) if is_valid and extracted else 0,
                "denied_symptoms": len(extracted.denied_symptoms) if is_valid and extracted else 0,
                "medical_history": len(extracted.medical_history_updates) if is_valid and extracted else 0,
                "medications": len(extracted.medication_updates) if is_valid and extracted else 0,
                "allergies": len(extracted.allergy_updates) if is_valid and extracted else 0,
                "inquiry_detected": extracted.patient_inquired_diagnosis_or_treatment if is_valid and extracted else False,
            })

        results.append({
            "scenario_id": scenario["id"],
            "scenario_name": scenario["name"],
            "avg_latency_ms": round(sum(r["latency_ms"] for r in scen_results) / len(scen_results), 2),
            "validity_rate": round(sum(1 for r in scen_results if r["is_valid"]) / len(scen_results) * 100.0, 1),
            "details": scen_results,
        })

    avg_overall_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
    total_evals = len(BENCHMARK_SCENARIOS) * iterations
    overall_validity = round((successes / total_evals) * 100.0, 1)

    return {
        "provider": provider_name,
        "available": True,
        "overall_validity_percent": overall_validity,
        "avg_latency_ms": avg_overall_latency,
        "scenarios": results,
    }


def print_markdown_summary(summary_list: List[Dict[str, Any]]):
    print("\n" + "=" * 80)
    print("           LLM EXTRACTION PROVIDER BENCHMARK REPORT")
    print("=" * 80 + "\n")

    print("### Summary Performance Comparison Table\n")
    print("| Provider | Availability | Overall Schema Validity | Avg Latency (ms) | Status |")
    print("| :--- | :--- | :--- | :--- | :--- |")

    for res in summary_list:
        prov = res["provider"]
        if not res.get("available", True):
            print(f"| `{prov}` | Unavailable | 0.0% | N/A | Error: {res.get('error')} |")
        else:
            valid_str = f"{res['overall_validity_percent']}%"
            lat_str = f"{res['avg_latency_ms']} ms"
            status = "PASSED" if res["overall_validity_percent"] == 100.0 else "WARNING"
            print(f"| `{prov}` | Available | {valid_str} | {lat_str} | {status} |")

    print("\n\n### Detailed Scenario Extraction Metrics\n")

    for res in summary_list:
        if not res.get("available", True):
            continue

        print(f"#### Provider: `{res['provider']}`")
        print("| Scenario ID | Scenario Name | Avg Latency (ms) | Schema Validity |")
        print("| :--- | :--- | :--- | :--- |")

        for scen in res["scenarios"]:
            print(f"| {scen['scenario_id']} | {scen['scenario_name']} | {scen['avg_latency_ms']} ms | {scen['validity_rate']}% |")
        print("\n")


def main():
    parser = argparse.ArgumentParser(description="Benchmark LLM Providers for Clinical Extraction")
    parser.add_argument(
        "--providers",
        type=str,
        default="mock,local",
        help="Comma-separated list of providers to evaluate (e.g., mock,local,gemini)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1,
        help="Number of iterations per test scenario",
    )
    args = parser.parse_args()

    providers_to_test = [p.strip().lower() for p in args.providers.split(",") if p.strip()]
    
    print(f"Starting LLM Extraction Benchmark across providers: {providers_to_test} ({args.iterations} iteration(s) per scenario)...")

    summaries = []
    for prov in providers_to_test:
        summary = evaluate_provider(prov, iterations=args.iterations)
        summaries.append(summary)

    print_markdown_summary(summaries)


if __name__ == "__main__":
    main()
