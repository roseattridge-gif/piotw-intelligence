# Restructuring cohort v2

Status: selection rules frozen before outcome review

## Eligible universe

UK-listed operating companies classified in industrials, manufacturing, engineering, aerospace/defence, automotive components, building/materials, electronics, industrial technology or closely related B2B production/services. Investment companies, pre-revenue shells and entities without stable operating identity are excluded.

The target is 100 companies with three prediction occasions each. Selection is independent of post-cutoff restructuring outcomes.

## Inclusion rules

- Listed and operating at the relevant cutoff.
- Stable entity mapping across source documents, allowing documented name/ticker changes.
- At least one primary annual/interim/trading disclosure published during the 15 months before cutoff.
- A company/results archive adequate to review the complete 12-month outcome window and first post-window results.
- At least one usable pressure or contrary evidence item; missing features remain invalid rather than silently zero-filled.
- No outcome knowledge used for inclusion, ordering or sector quota.

## Exclusion rules

- Acquisition, liquidation, reverse takeover or demerger makes the prediction target/entity uninterpretable at cutoff.
- No primary source with independently evidenced publication date.
- Historic documents are technically inaccessible and no legally usable archived copy can be verified.
- Duplicate economic entity or subsidiary already represented by its listed parent.
- Data-quality exclusion defined above; outcome-related exclusions after manifest freeze are prohibited.

## Sampling and composition

Construct a versioned candidate census, stratify into aerospace/defence/automotive, materials/building products, industrial engineering/equipment, and engineering/technology/services, then rank within stratum by SHA-256 of a fixed seed plus stable entity identifier. Take fixed proportional quotas totalling 100. Replacement follows the next hash in the same stratum and must cite an eligible data-quality exclusion.

Cutoffs are 31 December 2020 and 31 December 2022 for validation and 31 December 2024 for the untouched temporal holdout. Any v1 occasion is assigned to development, never validation. Each included company should contribute all eligible cutoffs; ineligible occasions are retained in the manifest with a reason.

## Bias

This design favours surviving listed companies with strong disclosure archives and may underrepresent failed, acquired, very small or poorly archived firms. Industrial-sector focus limits external validity. Repeated company observations are correlated; uncertainty and sensitivity therefore cluster by company. The sampling rule avoids selecting known restructurers but does not create a complete exchange census.
