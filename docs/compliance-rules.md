# SIH26034 Prototype Compliance Rules

## Scope
This file defines the engineering contract for the first vertical slice. It is NOT a final legal interpretation.

## Decision states
- PASS: declaration detected with adequate confidence and parsed by the prototype rule.
- FAIL: required declaration not detected in submitted content.
- REVIEW: declaration may exist but extraction/parsing confidence is inadequate.
- N/A: reserved for later applicability rules.

## V0.1 rules
| Rule | Field | Current prototype behavior | Legal verification status |
|---|---|---|---|
| LM-R001 | MRP | Detect common MRP wording + amount | Needs final official-rule verification |
| LM-R002 | Net quantity | Detect quantity + supported unit | Needs final official-rule verification |
| LM-R003 | Manufacturer/Packer/Importer | Detect common entity wording | Needs final official-rule verification |

## Next rules to verify before implementation
1. Consumer-care information
2. Common/generic name
3. Month/year or applicable date declaration
4. Unit sale price applicability
5. Country of origin applicability for imported packages
6. Best-before/use-by applicability
7. Readability vs absolute font-height verification
