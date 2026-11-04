# Protocol review and amendment, 2026-11-04

The initial v0.2 eight-attempt registry and results remain immutable.

Two task contracts were ambiguous on review, so their raw scores must not be interpreted as mechanics failures:

- S06 described final `adjust` as the string `"false"` in an illustrative schema, while the tool/evaluator required JSON boolean `false`. The agent used a boolean in the experiment and a string in its submission. Geometry/library decisions were correct. The protocol, not a mechanical mistake, explains the raw validation failure.
- S08 asked to rank by minimum force but omitted ascending versus descending. The agent explicitly chose descending (best-to-worst), while the hidden check expected ascending (weakest-first). Failure classification and recovery decisions were correct. This is a task-direction ambiguity.

Amendment v0.2.1 makes both contracts explicit, before two new DeepSeek/Pi protocol-validation attempts. Only S06/S08 are rerun, each once, with unchanged numerical physics, evaluator and budgets. The amendment freezes new source hashes and references the old registry hash. These are not replacements for budget failures and not a repeated performance study. No further API expansion is scheduled.

Initial S01 is a service RPM error; S03 reached its turn budget without submitting, despite computing a feasible vector; S07 exhausted its output budget. These records remain unchanged and receive no amendment retry.

公开说明：S06、S08初次题面存在输出类型及排序方向歧义，原始分数仅作诊断，不作为模型力学能力评分。更正题面后分别复核一次，保留新旧全部记录。未改动数值判分器，未对预算失败反复重试。

## Final review after the two checks

S06 passed its clarified contract. S08 correctly ranked and classified contact failures, but proposed refined re-solves of completed physical failures. The scorer expected `done` under a minimal-recovery policy; that complete policy was not stated in the amended prompt. Accordingly this raw zero is ALSO excluded as a policy-contract ambiguity, not interpreted as a mechanical mistake. No more model calls were made. Delivered v0.2.2 makes the policy explicit for future use; its final wording is not claimed to have a new agent trial. The independent numerical evaluator has not been changed.

Final accounting:10 retained attempts;4 passes,2 valid budget/non-submission failures,1 RPM environment error,3 protocol-ambiguity exclusions. Six capability-valid attempts remain. No model/harness ranking follows.
