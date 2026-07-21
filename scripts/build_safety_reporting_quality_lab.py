from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "analysis" / "outputs"
IMAGE_DIR = ROOT / "docs" / "images"

RNG = np.random.default_rng(230747)

REPORTS = [
    ("Daily Incident Intake", "daily", 7, "Safety Logic"),
    ("Weekly Exception Review", "weekly", 3, "Safety Logic"),
    ("Monthly Field Safety Scorecard", "monthly", 5, "Safety Logic"),
    ("Contractor Compliance Snapshot", "weekly", 4, "ISN"),
    ("Chemical SDS Coverage", "weekly", 4, "MSDS"),
    ("Vendor Credential Audit", "monthly", 6, "Browz"),
    ("PPE Readiness Tracker", "weekly", 4, "PICS"),
    ("Ad Hoc Leader Request", "ad_hoc", 2, "Corporate Request"),
]

DIVISIONS = ["Uniform Rental", "First Aid & Safety", "Fire Protection", "Facility Services"]
REGIONS = ["Great Lakes", "Midwest", "Northeast", "Southeast", "South Central", "West"]
SYSTEMS = ["Safety Logic", "MSDS", "ISN", "Browz", "PICS", "Corporate Request"]
EXCEPTION_TYPES = [
    "missing_location_id",
    "late_source_extract",
    "duplicate_incident_key",
    "unmapped_employee_partner",
    "missing_completion_date",
    "invalid_vendor_credential",
    "open_corrective_action",
    "rollout_training_gap",
]


def reset_dirs() -> None:
    for directory in (DATA_DIR, OUTPUT_DIR, IMAGE_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def make_locations() -> pd.DataFrame:
    rows = []
    location_id = 1001
    for region in REGIONS:
        for division in DIVISIONS:
            for idx in range(3):
                headcount = int(RNG.integers(38, 210))
                safety_lead_tenure = round(float(RNG.uniform(0.3, 8.0)), 1)
                support_tier = "high_touch" if headcount > 150 or region in ["Great Lakes", "Southeast"] else "standard"
                rows.append(
                    {
                        "location_id": f"LOC-{location_id}",
                        "region": region,
                        "division": division,
                        "service_branch": f"{region[:2].upper()}-{division.split()[0][:3].upper()}-{idx + 1}",
                        "employee_partners": headcount,
                        "support_tier": support_tier,
                        "safety_lead_tenure_years": safety_lead_tenure,
                        "go_live_wave": int(RNG.integers(1, 5)),
                    }
                )
                location_id += 1
    return pd.DataFrame(rows)


def make_report_runs(locations: pd.DataFrame) -> pd.DataFrame:
    calendar = pd.date_range("2026-01-01", "2026-06-30", freq="D")
    rows = []
    run_id = 1
    for run_date in calendar:
        for report_name, cadence, sla_hours, source_system in REPORTS:
            if cadence == "weekly" and run_date.weekday() != 0:
                continue
            if cadence == "monthly" and run_date.day != 5:
                continue
            if cadence == "ad_hoc" and RNG.random() > 0.16:
                continue

            sampled_locations = locations.sample(
                n=int(RNG.integers(18, 36)),
                replace=False,
                random_state=int(RNG.integers(1, 999_999)),
            )
            for _, location in sampled_locations.iterrows():
                base_delay = {
                    "daily": 3.5,
                    "weekly": 1.7,
                    "monthly": 2.8,
                    "ad_hoc": 0.9,
                }[cadence]
                risk_lift = 1.3 if location["support_tier"] == "high_touch" else 0.0
                source_lift = 1.6 if source_system in ["Browz", "PICS"] else 0.6 if source_system == "MSDS" else 0.0
                delay_hours = max(0.1, float(RNG.normal(base_delay + risk_lift + source_lift, 1.6)))
                completed_at = run_date + pd.Timedelta(hours=8 + delay_hours)
                sla_met = delay_hours <= sla_hours
                completeness = float(
                    np.clip(
                        RNG.normal(
                            0.972
                            - (0.018 if source_system in ["Browz", "PICS"] else 0)
                            - (0.011 if location["support_tier"] == "high_touch" else 0),
                            0.018,
                        ),
                        0.84,
                        0.999,
                    )
                )
                duplicate_keys = int(max(0, RNG.poisson(0.45 + (1.3 if source_system == "Safety Logic" else 0.1))))
                unmapped_records = int(max(0, RNG.poisson(1.6 + (2.2 if location["support_tier"] == "high_touch" else 0.4))))
                rows.append(
                    {
                        "run_id": f"RUN-{run_id:06d}",
                        "run_date": run_date.date().isoformat(),
                        "report_name": report_name,
                        "cadence": cadence,
                        "source_system": source_system,
                        "location_id": location["location_id"],
                        "region": location["region"],
                        "division": location["division"],
                        "support_tier": location["support_tier"],
                        "sla_hours": sla_hours,
                        "refresh_delay_hours": round(delay_hours, 2),
                        "sla_met": bool(sla_met),
                        "records_expected": int(RNG.integers(90, 420)),
                        "completeness_rate": round(completeness, 4),
                        "duplicate_keys": duplicate_keys,
                        "unmapped_records": unmapped_records,
                        "completed_at": completed_at.isoformat(),
                    }
                )
                run_id += 1
    return pd.DataFrame(rows)


def make_exceptions(report_runs: pd.DataFrame) -> pd.DataFrame:
    rows = []
    exception_id = 1
    for _, run in report_runs.iterrows():
        expected_exception_pressure = (
            (0.25 if not run["sla_met"] else 0.05)
            + max(0, (0.97 - run["completeness_rate"]) * 12)
            + min(run["duplicate_keys"], 4) * 0.11
            + min(run["unmapped_records"], 8) * 0.045
        )
        exception_count = int(RNG.poisson(expected_exception_pressure))
        for _ in range(exception_count):
            exception_type = str(RNG.choice(EXCEPTION_TYPES))
            severity = RNG.choice(["critical", "high", "medium", "low"], p=[0.08, 0.22, 0.48, 0.22])
            age_days = int(max(0, RNG.gamma(2.2, 2.4) + (4 if severity in ["critical", "high"] else 0)))
            closed = RNG.random() > (0.18 + (0.22 if severity in ["critical", "high"] else 0.06))
            owner_group = RNG.choice(["Corporate Safety", "Field Safety Lead", "Data Steward", "Vendor Coordinator"])
            rows.append(
                {
                    "exception_id": f"EXC-{exception_id:06d}",
                    "run_id": run["run_id"],
                    "run_date": run["run_date"],
                    "report_name": run["report_name"],
                    "source_system": run["source_system"],
                    "location_id": run["location_id"],
                    "region": run["region"],
                    "division": run["division"],
                    "exception_type": exception_type,
                    "severity": severity,
                    "owner_group": owner_group,
                    "age_days": age_days,
                    "status": "closed" if closed else "open",
                    "resolution_hours": round(float(RNG.normal(30, 12) + age_days * 6), 1) if closed else "",
                    "requires_field_followup": bool(exception_type in ["open_corrective_action", "rollout_training_gap", "unmapped_employee_partner"]),
                }
            )
            exception_id += 1
    return pd.DataFrame(rows)


def make_training_rollout(locations: pd.DataFrame) -> pd.DataFrame:
    modules = [
        ("Report Exception Intake", "safety_leads"),
        ("Daily Safety Report Refresh", "field_operations"),
        ("SDS and Vendor Source Updates", "field_operations"),
        ("Corrective Action Coding", "safety_leads"),
        ("Leader Request Triage", "business_leaders"),
    ]
    rows = []
    assignment_id = 1
    for _, location in locations.iterrows():
        for module, audience in modules:
            assigned = int(max(8, RNG.normal(location["employee_partners"] * 0.28, 12)))
            completion_bias = 0.08 * (location["go_live_wave"] - 1) - (0.05 if location["support_tier"] == "high_touch" else 0)
            completion_rate = float(np.clip(RNG.normal(0.86 - completion_bias, 0.08), 0.55, 0.99))
            completed = int(round(assigned * completion_rate))
            overdue = int(max(0, assigned - completed - RNG.integers(0, 5)))
            rows.append(
                {
                    "assignment_id": f"TRN-{assignment_id:05d}",
                    "location_id": location["location_id"],
                    "region": location["region"],
                    "division": location["division"],
                    "go_live_wave": location["go_live_wave"],
                    "module_name": module,
                    "audience": audience,
                    "assigned_employee_partners": assigned,
                    "completed_employee_partners": completed,
                    "overdue_employee_partners": overdue,
                    "completion_rate": round(completed / assigned, 4),
                }
            )
            assignment_id += 1
    return pd.DataFrame(rows)


def make_data_quality_checks(report_runs: pd.DataFrame) -> pd.DataFrame:
    rows = []
    check_id = 1
    check_types = [
        "location_id_present",
        "employee_partner_mapped",
        "incident_key_unique",
        "completion_date_present",
        "vendor_credential_current",
        "corrective_action_status_valid",
        "source_extract_arrived",
    ]
    sampled = report_runs.sample(n=min(1800, len(report_runs)), random_state=230747)
    for _, run in sampled.iterrows():
        for check_name in RNG.choice(check_types, size=3, replace=False):
            base_fail = {
                "location_id_present": 0.012,
                "employee_partner_mapped": 0.038,
                "incident_key_unique": 0.021,
                "completion_date_present": 0.026,
                "vendor_credential_current": 0.047,
                "corrective_action_status_valid": 0.031,
                "source_extract_arrived": 0.033,
            }[check_name]
            fail_rate = base_fail + (0.025 if run["source_system"] in ["Browz", "PICS"] else 0) + (0.018 if not run["sla_met"] else 0)
            records_tested = int(RNG.integers(75, 360))
            failed_records = int(RNG.binomial(records_tested, min(fail_rate, 0.18)))
            rows.append(
                {
                    "check_id": f"DQ-{check_id:06d}",
                    "run_id": run["run_id"],
                    "run_date": run["run_date"],
                    "report_name": run["report_name"],
                    "source_system": run["source_system"],
                    "location_id": run["location_id"],
                    "check_name": check_name,
                    "records_tested": records_tested,
                    "failed_records": failed_records,
                    "pass_rate": round(1 - failed_records / records_tested, 4),
                }
            )
            check_id += 1
    return pd.DataFrame(rows)


def make_support_requests(locations: pd.DataFrame) -> pd.DataFrame:
    rows = []
    request_id = 1
    request_types = ["ad_hoc_data_pull", "report_training", "exception_review", "metric_definition", "source_access"]
    start = pd.Timestamp("2026-01-01")
    for day in range(181):
        request_date = start + pd.Timedelta(days=day)
        daily_count = int(RNG.poisson(4.5 + (2.2 if request_date.weekday() == 0 else 0)))
        for _ in range(daily_count):
            location = locations.sample(n=1, random_state=int(RNG.integers(1, 999_999))).iloc[0]
            request_type = str(RNG.choice(request_types, p=[0.28, 0.2, 0.27, 0.13, 0.12]))
            priority = str(RNG.choice(["urgent", "standard", "low"], p=[0.14, 0.68, 0.18]))
            target_hours = 12 if priority == "urgent" else 48 if priority == "standard" else 96
            turnaround = max(1.0, float(RNG.normal(target_hours * 0.72, target_hours * 0.22)))
            if request_type in ["source_access", "exception_review"]:
                turnaround += float(RNG.uniform(4, 18))
            rows.append(
                {
                    "request_id": f"REQ-{request_id:05d}",
                    "request_date": request_date.date().isoformat(),
                    "location_id": location["location_id"],
                    "region": location["region"],
                    "division": location["division"],
                    "request_type": request_type,
                    "priority": priority,
                    "target_hours": target_hours,
                    "turnaround_hours": round(turnaround, 1),
                    "met_target": bool(turnaround <= target_hours),
                    "requester_group": str(RNG.choice(["Corporate Safety", "Field Operations", "Business Leader"], p=[0.28, 0.55, 0.17])),
                }
            )
            request_id += 1
    return pd.DataFrame(rows)


def write_source_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    locations = make_locations()
    report_runs = make_report_runs(locations)
    exceptions = make_exceptions(report_runs)
    training = make_training_rollout(locations)
    dq_checks = make_data_quality_checks(report_runs)
    requests = make_support_requests(locations)

    locations.to_csv(DATA_DIR / "field_locations.csv", index=False)
    report_runs.to_csv(DATA_DIR / "safety_report_runs.csv", index=False)
    exceptions.to_csv(DATA_DIR / "safety_report_exceptions.csv", index=False)
    training.to_csv(DATA_DIR / "report_rollout_training.csv", index=False)
    dq_checks.to_csv(DATA_DIR / "data_quality_checks.csv", index=False)
    requests.to_csv(DATA_DIR / "field_support_requests.csv", index=False)
    return report_runs, exceptions, training, dq_checks, requests


def build_outputs(
    report_runs: pd.DataFrame,
    exceptions: pd.DataFrame,
    training: pd.DataFrame,
    dq_checks: pd.DataFrame,
    requests: pd.DataFrame,
) -> dict[str, float]:
    report_runs["run_date"] = pd.to_datetime(report_runs["run_date"])
    exceptions["run_date"] = pd.to_datetime(exceptions["run_date"])
    requests["request_date"] = pd.to_datetime(requests["request_date"])

    run_count = len(report_runs)
    exception_rate = len(exceptions) / run_count
    sla_rate = report_runs["sla_met"].mean()
    completeness = report_runs["completeness_rate"].mean()
    open_high = len(exceptions[(exceptions["status"] == "open") & (exceptions["severity"].isin(["critical", "high"]))])
    training_completion = training["completed_employee_partners"].sum() / training["assigned_employee_partners"].sum()
    support_sla = requests["met_target"].mean()
    dq_pass = 1 - dq_checks["failed_records"].sum() / dq_checks["records_tested"].sum()

    report_summary = (
        report_runs.groupby(["report_name", "cadence", "source_system"], as_index=False)
        .agg(
            report_runs=("run_id", "count"),
            sla_adherence=("sla_met", "mean"),
            avg_refresh_delay_hours=("refresh_delay_hours", "mean"),
            avg_completeness=("completeness_rate", "mean"),
            duplicate_keys=("duplicate_keys", "sum"),
            unmapped_records=("unmapped_records", "sum"),
        )
        .round(4)
    )
    report_summary.to_csv(OUTPUT_DIR / "report_sla_quality_summary.csv", index=False)

    dq_summary = (
        dq_checks.groupby(["source_system", "check_name"], as_index=False)
        .agg(records_tested=("records_tested", "sum"), failed_records=("failed_records", "sum"))
        .assign(failure_rate=lambda df: df["failed_records"] / df["records_tested"])
        .sort_values("failure_rate", ascending=False)
        .round(4)
    )
    dq_summary.to_csv(OUTPUT_DIR / "data_quality_rule_summary.csv", index=False)

    exception_queue = (
        exceptions[exceptions["status"] == "open"]
        .groupby(["region", "division", "source_system", "exception_type", "severity", "owner_group"], as_index=False)
        .agg(open_exceptions=("exception_id", "count"), max_age_days=("age_days", "max"), field_followups=("requires_field_followup", "sum"))
        .assign(
            priority_score=lambda df: df["open_exceptions"] * 2
            + df["max_age_days"] * 0.7
            + df["field_followups"] * 1.5
            + df["severity"].map({"critical": 18, "high": 10, "medium": 4, "low": 1})
        )
        .sort_values("priority_score", ascending=False)
        .head(30)
        .round(2)
    )
    exception_queue.to_csv(OUTPUT_DIR / "field_exception_action_queue.csv", index=False)

    training_summary = (
        training.groupby(["region", "division", "go_live_wave"], as_index=False)
        .agg(assigned=("assigned_employee_partners", "sum"), completed=("completed_employee_partners", "sum"), overdue=("overdue_employee_partners", "sum"))
        .assign(completion_rate=lambda df: df["completed"] / df["assigned"])
        .sort_values("completion_rate")
        .round(4)
    )
    training_summary.to_csv(OUTPUT_DIR / "rollout_training_adoption_summary.csv", index=False)

    monthly = report_runs.assign(month=report_runs["run_date"].dt.to_period("M").astype(str)).groupby("month", as_index=False).agg(
        report_runs=("run_id", "count"),
        sla_adherence=("sla_met", "mean"),
        avg_completeness=("completeness_rate", "mean"),
        duplicate_keys=("duplicate_keys", "sum"),
        unmapped_records=("unmapped_records", "sum"),
    )
    monthly = monthly.merge(
        exceptions.assign(month=exceptions["run_date"].dt.to_period("M").astype(str)).groupby("month", as_index=False).agg(exceptions=("exception_id", "count")),
        on="month",
        how="left",
    ).fillna({"exceptions": 0})
    monthly["exception_rate_per_run"] = monthly["exceptions"] / monthly["report_runs"]
    monthly.round(4).to_csv(OUTPUT_DIR / "monthly_reporting_reliability.csv", index=False)

    support_summary = (
        requests.groupby(["request_type", "priority"], as_index=False)
        .agg(requests=("request_id", "count"), target_met_rate=("met_target", "mean"), avg_turnaround_hours=("turnaround_hours", "mean"))
        .sort_values(["target_met_rate", "requests"], ascending=[True, False])
        .round(4)
    )
    support_summary.to_csv(OUTPUT_DIR / "field_support_request_sla_summary.csv", index=False)

    headline = {
        "source_report_runs": int(run_count),
        "source_exceptions": int(len(exceptions)),
        "source_quality_checks": int(len(dq_checks)),
        "field_support_requests": int(len(requests)),
        "overall_exception_rate_per_report_run": round(float(exception_rate), 4),
        "recurring_report_sla_adherence": round(float(sla_rate), 4),
        "average_report_completeness": round(float(completeness), 4),
        "data_quality_pass_rate": round(float(dq_pass), 4),
        "open_high_or_critical_exceptions": int(open_high),
        "rollout_training_completion": round(float(training_completion), 4),
        "field_support_request_sla": round(float(support_sla), 4),
    }
    (OUTPUT_DIR / "headline_metrics.json").write_text(json.dumps(headline, indent=2) + "\n", encoding="utf-8")
    pd.DataFrame([headline]).to_csv(OUTPUT_DIR / "headline_metrics.csv", index=False)
    return headline


def plot_outputs() -> None:
    report_summary = pd.read_csv(OUTPUT_DIR / "report_sla_quality_summary.csv")
    dq_summary = pd.read_csv(OUTPUT_DIR / "data_quality_rule_summary.csv")
    exception_queue = pd.read_csv(OUTPUT_DIR / "field_exception_action_queue.csv")
    training_summary = pd.read_csv(OUTPUT_DIR / "rollout_training_adoption_summary.csv")
    monthly = pd.read_csv(OUTPUT_DIR / "monthly_reporting_reliability.csv")

    plt.style.use("seaborn-v0_8-whitegrid")

    fig, ax1 = plt.subplots(figsize=(10.8, 6.2))
    ax1.plot(monthly["month"], monthly["sla_adherence"] * 100, marker="o", color="#2563eb", label="SLA adherence")
    ax1.plot(monthly["month"], monthly["avg_completeness"] * 100, marker="s", color="#059669", label="Completeness")
    ax1.set_ylabel("Percent")
    ax1.set_ylim(86, 101)
    ax2 = ax1.twinx()
    ax2.bar(monthly["month"], monthly["exception_rate_per_run"], color="#f97316", alpha=0.28, label="Exceptions per run")
    ax2.set_ylabel("Exceptions per report run")
    ax1.set_title("Recurring Report SLA and Completeness Trend")
    ax1.set_xlabel("Month")
    lines, labels = ax1.get_legend_handles_labels()
    bars, bar_labels = ax2.get_legend_handles_labels()
    ax1.legend(lines + bars, labels + bar_labels, loc="lower left")
    fig.tight_layout()
    fig.savefig(IMAGE_DIR / "sla_completeness_trend.png", dpi=160)
    plt.close(fig)

    pivot = (
        dq_summary.pivot_table(index="check_name", columns="source_system", values="failure_rate", aggfunc="mean")
        .fillna(0)
        .sort_index()
    )
    fig, ax = plt.subplots(figsize=(10.8, 6.4))
    image = ax.imshow(pivot.values * 100, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(pivot.columns)), labels=pivot.columns, rotation=30, ha="right")
    ax.set_yticks(range(len(pivot.index)), labels=pivot.index)
    ax.set_title("Data Quality Failure Rate by Source System and Rule")
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            ax.text(j, i, f"{pivot.iloc[i, j] * 100:.1f}%", ha="center", va="center", fontsize=8)
    fig.colorbar(image, ax=ax, label="Failure rate")
    fig.tight_layout()
    fig.savefig(IMAGE_DIR / "data_quality_rule_heatmap.png", dpi=160)
    plt.close(fig)

    top = exception_queue.head(12).copy()
    top["queue_label"] = top["region"] + " / " + top["source_system"] + " / " + top["exception_type"]
    fig, ax = plt.subplots(figsize=(11.5, 7.2))
    colors = top["severity"].map({"critical": "#991b1b", "high": "#dc2626", "medium": "#f59e0b", "low": "#64748b"})
    ax.barh(top["queue_label"], top["priority_score"], color=colors)
    ax.invert_yaxis()
    ax.set_xlabel("Priority score")
    ax.set_title("Open Safety Report Exception Action Queue")
    for idx, row in top.reset_index(drop=True).iterrows():
        ax.text(row["priority_score"] + 0.6, idx, f"{int(row['open_exceptions'])} open, {int(row['max_age_days'])}d max age", va="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(IMAGE_DIR / "field_exception_action_queue.png", dpi=160)
    plt.close(fig)

    weakest = training_summary.head(12).copy()
    weakest["segment"] = weakest["region"] + " / " + weakest["division"] + " / wave " + weakest["go_live_wave"].astype(str)
    fig, ax = plt.subplots(figsize=(11.2, 6.7))
    ax.barh(weakest["segment"], weakest["completion_rate"] * 100, color="#0f766e")
    ax.invert_yaxis()
    ax.axvline(85, color="#ea580c", linestyle="--", linewidth=1.5, label="85% rollout guardrail")
    ax.set_xlim(50, 100)
    ax.set_xlabel("Training completion rate")
    ax.set_title("Lowest Rollout Training Adoption Segments")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(IMAGE_DIR / "rollout_training_adoption_gap.png", dpi=160)
    plt.close(fig)


def main() -> None:
    reset_dirs()
    report_runs, exceptions, training, dq_checks, requests = write_source_tables()
    headline = build_outputs(report_runs, exceptions, training, dq_checks, requests)
    plot_outputs()
    print(json.dumps(headline, indent=2))


if __name__ == "__main__":
    main()
