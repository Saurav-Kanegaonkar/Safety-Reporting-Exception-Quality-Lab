# Analysis Plan

## Objective

Build a repeatable safety reporting quality pack that helps corporate safety leaders and field operations answer three questions:

- Which recurring safety reports are late, incomplete, or noisy?
- Which exceptions should be handled first?
- Which rollout training and field support gaps are likely to keep reports unreliable?

## Stakeholders

- Corporate safety leaders need a reliable leadership pack and a concise list of quality risks.
- Field safety leads need specific exception queues and training follow-up lists.
- Business leaders need confidence that recurring and ad hoc safety data requests are timely and explainable.
- Data stewards need rule-level evidence for cleansing and source-system follow-up.

## Data Sourcing Choice

The project uses synthetic data because real safety management exports, employee-partner records, contractor compliance data, and internal exception logs are confidential and not available for public portfolio work. The synthetic process is documented in `scripts/build_safety_reporting_quality_lab.py` and avoids claims about real Cintas outcomes.

## Source Tables

- Field locations.
- Safety report runs.
- Safety report exceptions.
- Report rollout training.
- Data quality checks.
- Field support requests.

## Method

1. Generate a synthetic field-location network with regions, divisions, support tiers, and rollout waves.
2. Simulate report runs across daily, weekly, monthly, and ad hoc cadences.
3. Model refresh SLA performance, completeness, duplicate keys, and unmapped records.
4. Generate exceptions from SLA misses, completeness pressure, duplicate keys, and unmapped records.
5. Generate rollout training assignments and field support request performance.
6. Aggregate source tables into report-level, rule-level, queue-level, training-level, and support-level outputs.
7. Render evidence images that a safety reporting analyst could use in a leadership or field support conversation.

## EDA Coverage Checklist

- Row counts and source coverage by table.
- Report volume distribution by cadence, report name, source system, region, and division.
- Refresh-delay outlier checks by report and source system.
- SLA adherence and completeness trend checks by month.
- Data-quality failure rates by source system and rule.
- Open exception severity and aging checks by region, division, owner group, and exception type.
- Training adoption checks by go-live wave and operating segment.
- Field support request turnaround checks by request type and priority.

## Decision Rules

- Reports below 85 percent SLA adherence require cadence or source-system review.
- Quality rules above 5 percent failed records require cleansing backlog ownership.
- Open high or critical exceptions with field follow-up flags should be prioritized in the exception queue.
- Rollout training segments below 85 percent completion should receive targeted enablement before new report changes are expanded.
- Support request categories below 80 percent target adherence should receive clearer triage paths or templates.

## Outputs

- Headline metric file for quick inspection.
- Report SLA and data quality summaries for recurring reporting reliability.
- Exception action queue for field operations support.
- Rollout adoption summary for training follow-up.
- Support request SLA summary for internal-customer service quality.
- Four rendered evidence images embedded in the README.

## Validation

The artifact is intended to pass:

```bash
node scripts/validate_project_artifact.js outputs/projects/Safety-Reporting-Exception-Quality-Lab outputs/jobs/cintas-data-analyst-i
```
