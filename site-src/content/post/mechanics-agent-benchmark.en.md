---
title: "Testing Mechanical Decisions: An Agent Benchmark Development Pilot"
date: 2026-11-03
slug: "mechanics-agent-benchmark"
author: "AlexanderChan"
description: "Eight engineering task families, measured Kimi and DeepSeek/Pi pilot runs, observable traces and Tavotto figures. Two fixtures are executable in v0.1."
categories: ["Engineering"]
tags: ["Mechanics", "Agent", "Benchmark", "MCP", "LaTeX"]
connector_article: true
---
<article class="cae-article">
<p class="article-downloads"><a href="/articles/mechanics-agent-benchmark/benchmark_zh.pdf">中文 PDF</a> · <a href="/articles/mechanics-agent-benchmark/benchmark_en.pdf">English PDF</a> · <a href="/articles/mechanics-agent-benchmark/mechanics-benchmark-v0.1-source-evidence.zip">Code, tasks and complete traces</a></p>
<blockquote><p><strong>Development pilot, not a leaderboard.</strong> Eight task families are specified and two 1D mechanics fixtures execute. Four valid attempts yielded three passes and one output-budget exhaustion; two invalid setup attempts remain in the evidence. No evaluated 3D industrial solve is claimed.</p></blockquote>
<h2>From engineering experience to verifiable tasks</h2>
<p>Turn modeling, substructure partitioning, tolerance application, contact analysis and boundary search into executable tasks. Agents must operate tools and produce artifacts that survive independent numerical validation. Model, harness and tool configuration are recorded separately.</p>
<figure><a href="/articles/mechanics-agent-benchmark/architecture.pdf"><img src="/articles/mechanics-agent-benchmark/architecture.png" alt="Separate model, harness, tools and scoring; this pilot does not evaluate vendor solver tasks." loading="lazy" style="width:100%;height:auto"></a><figcaption>Separate model, harness, tools and scoring; this pilot does not evaluate vendor solver tasks.</figcaption></figure>
<h2>Eight task families</h2>
<div class="table-scroll"><table><thead><tr><th>ID</th><th>Task</th><th>State</th></tr></thead><tbody>
<tr><td>M01</td><td>Load, units and equilibrium</td><td>Fixture executable</td></tr>
<tr><td>M02</td><td>Mechanics-driven mesh allocation</td><td>Specified only</td></tr>
<tr><td>M03</td><td>Nonlinear preload and contact</td><td>Specified only</td></tr>
<tr><td>M04</td><td>Autonomous substructure partition</td><td>Fixture executable</td></tr>
<tr><td>M05</td><td>Bounded manufacturing variables</td><td>Specified only</td></tr>
<tr><td>M06</td><td>Library reuse and interface integrity</td><td>Specified only</td></tr>
<tr><td>M07</td><td>Pose failure-boundary search</td><td>Specified only</td></tr>
<tr><td>M08</td><td>Failure recovery and trusted ranking</td><td>Specified only</td></tr>
</tbody></table></div>
<h2>Importance must be justified mechanically</h2>
<p>The executable partition fixture preserves active bilinear regions, condenses a contiguous linear segment and retains interface DOFs. Low stress alone does not establish irrelevance. Validate the target response over the load envelope; the figure demonstrates only this public 1D fixture.</p>
<figure><a href="/articles/mechanics-agent-benchmark/partition.pdf"><img src="/articles/mechanics-agent-benchmark/partition.png" alt="Partition and load-envelope checks, not connector experimental curves." loading="lazy" style="width:100%;height:auto"></a><figcaption>Partition and load-envelope checks, not connector experimental curves.</figcaption></figure>
<h2>Measured pilot and uncertainty</h2>
<div class="table-scroll"><table><thead><tr><th>Task</th><th>Configuration</th><th>s</th><th>Outcome</th></tr></thead><tbody>
<tr><td>M01</td><td>Pi + DeepSeek</td><td>6.88</td><td>passed</td></tr>
<tr><td>M04</td><td>Pi + DeepSeek</td><td>16.36</td><td>passed</td></tr>
<tr><td>M01</td><td>mini + Kimi</td><td>37.25</td><td>passed</td></tr>
<tr><td>M04</td><td>mini + Kimi</td><td>122.72</td><td>output_budget_exhausted</td></tr>
</tbody></table></div>
<figure><a href="/articles/mechanics-agent-benchmark/pilot.pdf"><img src="/articles/mechanics-agent-benchmark/pilot.png" alt="Four valid pilot attempts, not evidence for a model or harness ranking." loading="lazy" style="width:100%;height:auto"></a><figcaption>Four valid pilot attempts, not evidence for a model or harness ranking.</figcaption></figure>
<p>The configured kimi-k2.5 route was unavailable; the pilot explicitly selected catalog-listed kimi-k2.6. DeepSeek used request ID deepseek-v4-flash through Pi SDK 0.73.1. Output was capped at 4096 tokens per request. Model and harness change together, preventing causal attribution. Actual API invoices are unknown; SDK zero-cost fields do not imply free usage.</p>
<h2>Evidence and next steps</h2>
<p>The bundle retains all attempts, queries, observable requests/outputs, tool interactions, numerical artifacts, independent checks, bilingual appendices and hashes. It excludes keys, the CCS database and private industrial models. A separate read-only probe verified 54 tools across three CAE MCP services; setup work is not agent evaluation. Next come public 3D fixtures and validators for the remaining six families, followed by a preregistered repeated campaign.</p>
<p><a href="/articles/mechanics-agent-benchmark/pilot_summary.csv">Pilot CSV</a> · <a href="/articles/mechanics-agent-benchmark/pilot_summary.json">Pilot JSON</a> · <a href="/articles/mechanics-agent-benchmark/mechanics-benchmark-v0.1-source-evidence.zip">Source / evidence ZIP</a></p>
</article>