---
title: "让 Agent 跑通 CAE：连接 HyperMesh、Abaqus 与 ParaView"
date: 2026-10-18T00:00:00+08:00
slug: "cae-mcp"
description: "三个 MCP、54 个工具，以及一个真实端子接触案例：原生前后处理、C++ ODB 转换、资源分配、错误修复与三组工程任务实测。"
categories: ["Engineering"]
tags: ["CAE", "MCP", "Abaqus", "HyperMesh", "ParaView"]
cae_article: true
---
<article class="cae-article">
<p class="article-downloads"><a href="/assets/cae-mcp/cae-mcp.pdf">PDF 阅读</a> · <a href="/assets/cae-mcp/cae-mcp-sources.zip">LaTeX / Tavotto 图源与数据</a> · <a href="/assets/cae-mcp/engineering-query.txt">完整 query 整理版</a> · <a href="/assets/cae-mcp/task_metrics.csv">实测统计 CSV</a></p><blockquote>
<p>给 Agent 一个端子模型和两步加载要求，它能否检查模型、安排计算资源、完成求解，再交回可核对的曲线与云图？这个项目把 HyperMesh、Abaqus 和 ParaView 连接为三个 MCP 服务，在一个真实端子接触案例上跑通了这条链路。三组独立实测均完成两步计算；启用 MCP 与工程规程的一组耗时 21.82 分钟，得到 108 帧结果与约 1.434141 N 的驱动力峰值。</p>
</blockquote><nav class="article-toc" aria-label="文章目录"><details><summary>文章目录（12 节）</summary><ol><li><a href="#从一句工况描述开始">从一句工况描述开始</a></li><li><a href="#三个-mcp54-个工具">三个 MCP，54 个工具</a></li><li><a href="#长任务需要持久状态与实际文件">长任务需要持久状态与实际文件</a></li><li><a href="#把-odb-转换做成独立的-c-工具">把 ODB 转换做成独立的 C++ 工具</a></li><li><a href="#计算资源如何自动选择">计算资源如何自动选择</a></li><li><a href="#报错以后先读证据再生成新输入">报错以后，先读证据，再生成新输入</a></li><li><a href="#材料与截面库以及-skill-的位置">材料与截面库，以及 Skill 的位置</a></li><li><a href="#端子案例从模型检查到后处理">端子案例：从模型检查到后处理</a></li><li><a href="#三组独立实测都完成了差别在哪里">三组独立实测：都完成了，差别在哪里</a></li><li><a href="#完成计算以后仍需保留哪些工程事实">完成计算以后，仍需保留哪些工程事实</a></li><li><a href="#输入query-与可复核资料">输入、query 与可复核资料</a></li><li><a href="#实现所依据的原生接口">实现所依据的原生接口</a></li></ol></details></nav>
<h2 id="从一句工况描述开始">从一句工况描述开始</h2>
<p>传统 CAE 自动化通常从一段脚本开始：导入模型、定义集合、提交作业、提取结果。Agent 让脚本生成变得容易，但工程任务的难点往往出现在脚本之外：口述里的“右端”对应哪个区域，应用进程退出是否意味着求解成功，外推节点应力能否与积分点应力直接比较，失败后改了什么，以及下一步究竟应该读取哪个文件。</p>
<p>我把这些问题作为工具接口的一部分。Agent 解释目标并选择动作；工具检查输入、调用原生应用、保存日志并返回实际产物。本文重点是执行的可靠性和可追溯性，数值结果均来自已完成的工程任务，测量日期为 2026 年 10 月 12 日。</p>
<p>端子案例的要求可以概括为：保留已有材料、截面与网格，固定 male 根部和 shield 根部，plate 先沿全局 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>+</mi><mi>Y</mi></mrow><annotation encoding="application/x-tex">+Y</annotation></semantics></math> 预压 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>0.3348</mn><mspace width="0.167em"></mspace><mrow><mi mathvariant="normal">m</mi><mi mathvariant="normal">m</mi></mrow></mrow><annotation encoding="application/x-tex">0.3348\,\mathrm{mm}</annotation></semantics></math>，再与 female 一起沿全局 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>−</mi><mi>Z</mi></mrow><annotation encoding="application/x-tex">-Z</annotation></semantics></math> 移动 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>10</mn><mspace width="0.167em"></mspace><mrow><mi mathvariant="normal">m</mi><mi mathvariant="normal">m</mi></mrow></mrow><annotation encoding="application/x-tex">10\,\mathrm{mm}</annotation></semantics></math>，摩擦系数为 0.13。这里的位置、方向和集合均经过确认。对新的“左边”“向下”等模糊描述，先展示候选区域与坐标解释，确认后再修改工况。</p>
<h2 id="三个-mcp54-个工具">三个 MCP，54 个工具</h2>
<p>MCP 提供 Agent 调用工具的协议。这个项目按应用分成三个服务，共用执行底座：HyperMesh 负责几何和网格，Abaqus 负责模型、求解与 ODB，ParaView 负责结果检查和可视化。</p>
<figure data-latex-placement="H">
<a href="/assets/cae-mcp/architecture.png" target="_blank" rel="noopener" aria-label="查看architecture原图"><img src="/assets/cae-mcp/architecture.png" width="1980" height="1144" loading="lazy" decoding="async" alt="Agent、三个原生应用 MCP 与共享 dispatcher 的架构" /></a>
<figcaption>按原生应用划分工具边界，底层共享任务状态、输入快照和产物记录。本文示意图与统计图均由可编辑脚本交给 Tavotto 执行、合版并导出。</figcaption>
</figure>
<div class="table-scroll" role="region" tabindex="0" aria-label="数据表，可横向滚动"><table>
<caption>服务范围与已经实现的能力</caption>
<thead>
<tr>
<th style="text-align: left;">服务</th>
<th style="text-align: right;">工具数</th>
<th style="text-align: left;">能力</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">HyperMesh</td>
<td style="text-align: right;">13</td>
<td style="text-align: left;">STEP 导入、HM 检查、平面切分、四面体网格、Abaqus INP 导出和高级 Tcl。</td>
</tr>
<tr>
<td style="text-align: left;">Abaqus</td>
<td style="text-align: right;">29</td>
<td style="text-align: left;">材料与截面库、区域检查、工况准备、资源计划、提交求解、错误诊断、修复、ODB 检查及转换。</td>
</tr>
<tr>
<td style="text-align: left;">ParaView</td>
<td style="text-align: right;">12</td>
<td style="text-align: left;">数据数组与帧检查、渲染、切片、线采样、图片返回和高级 Python。</td>
</tr>
</tbody>
</table></div>
<p>每个服务包含六个通用工具：能力检测、任务状态、任务列表、产物列表、日志读取和取消。因此 54 是工具总数，包含按服务提供的通用管理接口，不能理解为 54 种独立求解算法。完整清单随文章源码提供。</p>
<p>应用脚本在各自的运行环境执行：HyperMesh 2017 使用 Tcl；Abaqus 2025 使用自己的 Python 或 C++ SDK；ParaView 6.1 使用 <code>pvpython</code>。普通 Python 服务处理协议、排队和输入检查，避免直接混用商业软件的二进制 API 与解释器。</p>
<p>为什么保留三个 MCP？因为几何、求解和后处理有不同的输入契约、运行时和失败方式。资源管理则放进 Abaqus 服务，避免多个服务分别计算、重复占用同一份求解预算。独立 ODB2VTK 也可以绕过 MCP 直接使用。</p>
<h2 id="长任务需要持久状态与实际文件">长任务需要持久状态与实际文件</h2>
<p>工具受理一个长任务后返回 <code>job_id</code>，而非阻塞到求解结束。后台 dispatcher 独立管理执行进程，客户端通过状态工具继续跟踪。只有任务进入 <code>succeeded</code>，才能把返回的真实产物路径交给下游；<code>queued</code> 和 <code>running</code> 都不表示完成。</p>
<p>每次任务保存请求、设置快照、原生脚本、日志、状态和结果索引。INP 依赖的 INCLUDE 文件递归复制，并记录 SHA256。资源计划也绑定输入闭包；排队期间源文件变化时，原计划不能静默用于新的输入。源模型保持只读，修复和重试产生新文件。</p>
<p>Abaqus 的完整成功检查同时要求原生完成标记、两步到达指定终点，以及非空、已关闭的新 ODB。ODB 文件存在，或者某个增量收敛，都不足以说明完整任务完成。ParaView 还要核对真实数组、帧数和取值范围，不能只交一张看起来合理的图片。</p>
<p>Windows 上还有进程生命周期问题：客户端退出可能连带结束其子进程。独立 dispatcher 的意义是让已经受理的求解不依附于一次工具调用的连接寿命。它承担本地执行管理，不替代操作系统或集群调度器。</p>
<h2 id="把-odb-转换做成独立的-c-工具">把 ODB 转换做成独立的 C++ 工具</h2>
<p>ODB2VTK 使用 Abaqus 官方 C++ ODB API，通过 <a href="https://docs.software.vt.edu/abaqusv2025/English/SIMACAECMDRefMap/simacmd-c-odbintrobulkdatacpp.htm"><code>bulkDataBlocks()</code></a> 连续读取字段，避免逐个 FieldValue 对象访问。网格、节点标签映射和 section assignment 只构造一次，跨帧复用。输出采用二进制 VTU，并用 PVD 索引选定帧。</p>
<p>命令行支持 <code>inspect</code>、<code>menu</code> 和 <code>convert</code>。未显式指定时，从 ODB 检测最后一个有帧的分析步、末帧、所有非空实例，以及存在的 <code>U</code> 和 <code>S:MISES</code>。也能选择多个分析步、帧列表或范围、section point、输出位置、变形倍率和复数实部或虚部。</p>
<pre><code>.\native\odb2vtk\odb2vtk.cmd inspect --odb &quot;input.odb&quot;
.\native\odb2vtk\odb2vtk.cmd menu --odb &quot;input.odb&quot;
.\native\odb2vtk\odb2vtk.cmd convert --odb &quot;input.odb&quot; --step all --frames all --fields &quot;U,S:MISES&quot; --avg 75 --regions section --output &quot;exports\terminal&quot;</code></pre>
<p>转换结果包含逐帧 VTU、<code>collection.pvd</code> 和 <code>manifest.json</code>。ODB 按只读打开，缺失值保留 NaN，未知单元默认报错，旧 ODB 不会被隐式升级。Windows 启动器负责设置当前进程的 Abaqus DLL 搜索路径；迁移机器时仍需匹配的原生运行库。</p>
<h3 id="avg-75-的关键是区域和计算顺序">Avg 75 的关键是区域和计算顺序</h3>
<p>依照 <a href="https://docs.software.vt.edu/abaqusv2025/English/SIMACAECAERefMap/simacae-c-resconceptaverage.htm">Abaqus/CAE 的默认区域定义</a>，这里的平均区域是实际 <strong>section assignment</strong>，不是仅按材料名或 section 名合并。两个 assignment 即使引用相同 section，也保留各自边界。缺少 assignment 的单元被隔离并报告，避免猜测连续区域。</p>
<p>对 Mises 等标量，处理顺序是：外推张量到单元节点，计算标量，再按区域和阈值决定是否平均。对某一节点的有效贡献值，差异百分比定义为 <math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>v</mi><mo>=</mo><mn>100</mn><mfrac><mrow><msub><mi>s</mi><mi mathvariant="normal">max</mi></msub><mo>−</mo><msub><mi>s</mi><mi mathvariant="normal">min</mi></msub></mrow><mrow><msub><mi>S</mi><mrow><mrow><mi mathvariant="normal">max</mi><mo>&#8289;</mo></mrow><mo>,</mo><mi>R</mi></mrow></msub><mo>−</mo><msub><mi>S</mi><mrow><mrow><mi mathvariant="normal">min</mi><mo>&#8289;</mo></mrow><mo>,</mo><mi>R</mi></mrow></msub></mrow></mfrac><mo>,</mo></mrow><annotation encoding="application/x-tex">v=100\frac{s_{\max}-s_{\min}}
{S_{\max,R}-S_{\min,R}},</annotation></semantics></math> 其中分母取当前平均区域内全部有效外推值的范围，分子取该节点的贡献范围。在非退化区域内，<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>v</mi><mo>&lt;</mo><mn>75</mn></mrow><annotation encoding="application/x-tex">v&lt;75</annotation></semantics></math> 时做等权平均；等于阈值时保留不连续值。区域范围为零且贡献相等时，正阈值允许平均。阈值为 0 或 off 则关闭平均。</p>
<figure data-latex-placement="H">
<a href="/assets/cae-mcp/averaging.png" target="_blank" rel="noopener" aria-label="查看averaging原图"><img src="/assets/cae-mcp/averaging.png" width="1980" height="759" loading="lazy" decoding="async" alt="外推张量、计算标量、按 section assignment 和 Avg75 阈值平均" /></a>
<figcaption>先计算标量、再测试阈值。跨 assignment 或拒绝平均的位置保留独立的共位点，NodeLabel 仍能追溯原 ODB 节点。</figcaption>
</figure>
<p>结果数组包括 <code>S_MISES_Avg</code>、差异百分比、是否实际平均以及 <code>SectionAssignmentId</code>。后处理阶段不再插入 Clean/Merge Points，也不额外做 Cell Data to Point Data，避免抹去导出时保留的边界。</p>
<p>这实现了 section assignment 下的 scalar-before-average；壳/膜 feature-edge 附加边界和 tensor-after-average 模式没有在这里复刻。积分点结果与外推节点显示值也必须分开：同一末帧的原积分点最大 Mises 为约 644.00 MPa，而 Avg 75 外推节点显示峰值约为 1355.07 MPa，两者不是同一个测量位置。</p>
<h2 id="计算资源如何自动选择">计算资源如何自动选择</h2>
<p>资源工具先扫描 INP、INCLUDE 和装配实例，读取节点数、单元类型、分析过程、接触和 NLGEOM。重复实例按实际装配规模计数。对本例实体网格，用 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>3</mn><msub><mi>N</mi><mrow><mi mathvariant="normal">n</mi><mi mathvariant="normal">o</mi><mi mathvariant="normal">d</mi><mi mathvariant="normal">e</mi></mrow></msub></mrow><annotation encoding="application/x-tex">3N_{\mathrm{node}}</annotation></semantics></math> 作为自由度规模代理；存在接触时乘以 1.5，得到加权规模 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>D</mi><annotation encoding="application/x-tex">D</annotation></semantics></math>。它不是约束消元后的真实方程数。</p>
<p>CPU 基础档位为 <math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>c</mi><mn>0</mn></msub><mo stretchy="false" form="prefix">(</mo><mi>D</mi><mo stretchy="false" form="postfix">)</mo><mo>=</mo><mrow><mo stretchy="true" form="prefix">{</mo><mtable><mtr><mtd columnalign="left" style="text-align: left"><mn>1</mn><mo>,</mo></mtd><mtd columnalign="left" style="text-align: left"><mi>D</mi><mo>&lt;</mo><mn>50</mn><mo>,</mo><mn>000</mn><mo>,</mo></mtd></mtr><mtr><mtd columnalign="left" style="text-align: left"><mn>2</mn><mo>,</mo></mtd><mtd columnalign="left" style="text-align: left"><mn>50</mn><mo>,</mo><mn>000</mn><mo>≤</mo><mi>D</mi><mo>&lt;</mo><mn>200</mn><mo>,</mo><mn>000</mn><mo>,</mo></mtd></mtr><mtr><mtd columnalign="left" style="text-align: left"><mn>4</mn><mo>,</mo></mtd><mtd columnalign="left" style="text-align: left"><mn>200</mn><mo>,</mo><mn>000</mn><mo>≤</mo><mi>D</mi><mo>&lt;</mo><mn>750</mn><mo>,</mo><mn>000</mn><mo>,</mo></mtd></mtr><mtr><mtd columnalign="left" style="text-align: left"><mn>8</mn><mo>,</mo></mtd><mtd columnalign="left" style="text-align: left"><mi>D</mi><mo>≥</mo><mn>750</mn><mo>,</mo><mn>000</mn><mi>.</mi></mtd></mtr></mtable></mrow></mrow><annotation encoding="application/x-tex">c_0(D)=\begin{cases}
1,&amp;D&lt;50{,}000,\\
2,&amp;50{,}000\le D&lt;200{,}000,\\
4,&amp;200{,}000\le D&lt;750{,}000,\\
8,&amp;D\ge750{,}000.
\end{cases}</annotation></semantics></math> 最终档位还受物理核、项目预算、用户限制和已配置的许可证额度约束。内存上限按规模采用 15%、30%、50% 档位，并结合可用内存和共享预算裁剪。<code>abaqus_plan_resources</code> 只生成计划，<code>abaqus_submit_job</code> 消费计划并在启动时再次核验。</p>
<figure data-latex-placement="H">
<a href="/assets/cae-mcp/resources.png" target="_blank" rel="noopener" aria-label="查看resources原图"><img src="/assets/cae-mcp/resources.png" width="1980" height="748" loading="lazy" decoding="async" alt="按加权自由度分档的资源规则及输入绑定和预算预留" /></a>
<figcaption>左图是资源规则的计算结果，不是多核加速实测。右图说明计划如何绑定输入、预留预算并进入原生求解。</figcaption>
</figure>
<p>本例选取 2 CPU、15% 内存上限。比较实验也给所有组相同的上限，使用纯线程配置，避免把资源差异混入工具比较。共享预留保证本工具启动的并发求解满足 CPU 和内存总预算；预算不足则排队，任务结束后释放。</p>
<p>这是一套透明、可解释的初始分配规则，还没有通过多规模、多 CPU 档位的重复实验寻找最优值。根据 <a href="https://docs.software.vt.edu/abaqusv2025/English/SIMACAEEXCRefMap/simaexc-c-analysisproc.htm">Abaqus 作业参数定义</a>，Standard 的 memory 是可分配上限；Explicit 分析阶段的实际内存也不能按同一个参数理解。系统不接管外部启动的求解，也没有把配置中的许可证上限冒充为实时许可证池查询。</p>
<h2 id="报错以后先读证据再生成新输入">报错以后，先读证据，再生成新输入</h2>
<p><code>abaqus_diagnose_job</code> 读取真正的 <code>.dat</code>、<code>.msg</code>、<code>.sta</code> 和日志，返回有界原文、文件哈希、分类以及适用的修复动作。未知错误保留未知，不凭关键词猜一个“万能修复”。</p>
<p><code>abaqus_repair_job</code> 的自动范围刻意收窄：在有诊断依据时降低初始静力增量或提高最大增量数，保存新 INP、差异和修改清单，再做资源计划与 datacheck。它不改变总载荷、材料、摩擦、固定位置或总步长。涉及物理条件的改动仍需明确确认。</p>
<p>端子产品组第一次 datacheck 实际遇到的是空节点面定义。Agent 根据原生日志确认该空 surface 未被使用，通过高级脚本注释该定义、移除一处空行，保留修改差异，再通过检查并完成求解。这次修复体现的是诊断工具与原生脚本协作，不能把它描述成受限数值修复工具已经覆盖所有语法问题。</p>
<h2 id="材料与截面库以及-skill-的位置">材料与截面库，以及 Skill 的位置</h2>
<p>已有材料可能来自 INP、CAE 或 HyperMesh 模型。库工具采用“提取预览、再提交”的方式导入，保存原始 keyword、声明单位、来源和修订记录。更新记录时要求 <code>expected_revision</code>，截面引用指定材料修订，避免一次覆盖让历史任务失去原参数。导出时再把库内定义绑定到明确的 ELSET；单位不会被静默换算。</p>
<p>现有四面体工况模板支持其定义范围内的均质实体截面。复合截面、未知 keyword 或无法解析的方向定义会拒绝或报告遗漏。本文端子模型沿用原材料与截面，未为其补造演示弹性参数。</p>
<p>Skill 解决的是编排规程：先检查单位和集合，遇到模糊空间描述先确认，等待长任务成功，再使用实际产物，保持平均边界，解释原生警告，并保留失败尝试。它让 Agent 更稳定地使用已有工具；确定性校验仍留在 MCP 内，避免只靠提示词维持正确性。对比中的产品组同时启用了 MCP 和工程规程，实验没有单独隔离 Skill 的贡献。</p>
<h2 id="端子案例从模型检查到后处理">端子案例：从模型检查到后处理</h2>
<p>输入是一份已有网格的单对端子 INP，以及从整体装配提取的 HM 伴随模型。一件 female 对两片 male，另含 shield 与 prepress plate。INP 是网格编号、材料、截面及八对接触定义的权威来源，HM 用于原生模型检查；两者的节点编号不互相替代。</p>
<p>模型有 11,240 个 C3D10M 单元。male 根部两个集合各 21 个节点，shield 根部 159 个节点，共固定 201 个根部节点。female 通过 72 个节点的控制区域与 RP 耦合；plate 节点面含 1061 个节点，并耦合到独立 RP。</p>
<div class="table-scroll" role="region" tabindex="0" aria-label="数据表，可横向滚动"><table>
<caption>已经确认的两步工况，采用 mm–N–MPa 单位与全局坐标</caption>
<thead>
<tr>
<th style="text-align: left;">设置</th>
<th style="text-align: left;">数值或定义</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">Prepress</td>
<td style="text-align: left;">plate 的 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>U</mi><mn>2</mn></msub><mo>=</mo><mi>+</mi><mn>0.3348</mn></mrow><annotation encoding="application/x-tex">U_2=+0.3348</annotation></semantics></math> mm，<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>U</mi><mn>3</mn></msub><mo>=</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">U_3=0</annotation></semantics></math>；female 保持不动。</td>
</tr>
<tr>
<td style="text-align: left;">Insertion</td>
<td style="text-align: left;">保持 plate 的 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>U</mi><mn>2</mn></msub><annotation encoding="application/x-tex">U_2</annotation></semantics></math>；plate 与 female 同步 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>U</mi><mn>3</mn></msub><mo>=</mo><mi>−</mi><mn>10</mn></mrow><annotation encoding="application/x-tex">U_3=-10</annotation></semantics></math> mm。</td>
</tr>
<tr>
<td style="text-align: left;">接触</td>
<td style="text-align: left;">摩擦系数 0.13，硬接触，有限滑移，NLGEOM=YES。</td>
</tr>
<tr>
<td style="text-align: left;">静力控制</td>
<td style="text-align: left;">两步初始增量 0.01，总步长 1，最小增量 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msup><mn>10</mn><mrow><mi>−</mi><mn>8</mn></mrow></msup><annotation encoding="application/x-tex">10^{-8}</annotation></semantics></math>，最大增量 0.05，最大增量数 10000。</td>
</tr>
<tr>
<td style="text-align: left;">其余约束</td>
<td style="text-align: left;">RP 转动和未驱动平移分量保持固定；male 与 shield 根部平移固定。</td>
</tr>
</tbody>
</table></div>
<p>执行顺序为：HyperMesh 检查伴随模型，核对 INP 网格与区域，生成两步新输入，创建资源计划，运行 datacheck，处理真实报错，再提交完整求解。完成后直接读取新 ODB 的控制点 history、能量和原积分点结果，再转换全部分析步和帧，由 ParaView 核对并渲染。</p>
<figure data-latex-placement="H">
<a href="/assets/cae-mcp/terminal_states.png" target="_blank" rel="noopener" aria-label="查看terminal_states原图"><img src="/assets/cae-mcp/terminal_states.png" width="1980" height="2552" loading="lazy" decoding="async" alt="端子预压与插入终点的实际 ParaView 应力云图" /></a>
<figcaption>产品组新求解结果的两步终点，ParaView 原生渲染后由 Tavotto 合版。变形倍率为 1，各图保留自己的实际色标；视角整理不计入 Agent 任务耗时。</figcaption>
</figure>
<p>这里保留已有网格，前处理完成的是模型检查、区域核对、耦合与加载准备。工具链具备 STEP 导入、几何切分及四面体网格功能，但本例没有以 CAD 自动重划网格并重建全部接触作为实测起点。两步也只包含预压与插入，没有另行添加拔出。</p>
<h3 id="用数值定义结果">用数值定义结果</h3>
<p>驱动力取两个运动 RP 的全局反力，投影到插入方向： <math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>F</mi><mrow><mi mathvariant="normal">i</mi><mi mathvariant="normal">n</mi><mi mathvariant="normal">s</mi></mrow></msub><mo>=</mo><mi>−</mi><mo stretchy="false" form="prefix">(</mo><mi>R</mi><msub><mi>F</mi><mrow><mn>3</mn><mo>,</mo><mrow><mi mathvariant="normal">f</mi><mi mathvariant="normal">e</mi><mi mathvariant="normal">m</mi><mi mathvariant="normal">a</mi><mi mathvariant="normal">l</mi><mi mathvariant="normal">e</mi></mrow></mrow></msub><mo>+</mo><mi>R</mi><msub><mi>F</mi><mrow><mn>3</mn><mo>,</mo><mrow><mi mathvariant="normal">p</mi><mi mathvariant="normal">l</mi><mi mathvariant="normal">a</mi><mi mathvariant="normal">t</mi><mi mathvariant="normal">e</mi></mrow></mrow></msub><mo stretchy="false" form="postfix">)</mo><mi>.</mi></mrow><annotation encoding="application/x-tex">F_{\mathrm{ins}}=-(RF_{3,\mathrm{female}}+RF_{3,\mathrm{plate}}).</annotation></semantics></math> 这避免把接触两侧的内部力重复相加。产品组的新 ODB 包含 25 个 Prepress 帧与 83 个 Insertion 帧，共 108 帧；两步均达到终点，控制位移与给定值一致。</p>
<div class="table-scroll" role="region" tabindex="0" aria-label="数据表，可横向滚动"><table>
<caption>独立读取产品组新 ODB 得到的主要指标</caption>
<thead>
<tr>
<th style="text-align: left;">指标</th>
<th style="text-align: right;">数值</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">预压终点 plate <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>U</mi><mn>2</mn></msub><annotation encoding="application/x-tex">U_2</annotation></semantics></math>（mm）</td>
<td style="text-align: right;">0.334800005</td>
</tr>
<tr>
<td style="text-align: left;">插入终点 female / plate <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>U</mi><mn>3</mn></msub><annotation encoding="application/x-tex">U_3</annotation></semantics></math>（mm）</td>
<td style="text-align: right;"><math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>−</mi><mn>10</mn><mi>/</mi><mo>−</mo><mn>10</mn></mrow><annotation encoding="application/x-tex">-10 / -10</annotation></semantics></math></td>
</tr>
<tr>
<td style="text-align: left;">驱动力峰值（N）</td>
<td style="text-align: right;">1.434141</td>
</tr>
<tr>
<td style="text-align: left;">终点驱动力（N）</td>
<td style="text-align: right;">0.974671</td>
</tr>
<tr>
<td style="text-align: left;">末帧原积分点最大 Mises（MPa）</td>
<td style="text-align: right;">644.000061</td>
</tr>
<tr>
<td style="text-align: left;">末帧最大 PEEQ</td>
<td style="text-align: right;">0.009152083</td>
</tr>
<tr>
<td style="text-align: left;">末帧全储存 RF 三分量余额最大绝对值（N）</td>
<td style="text-align: right;"><math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mn>1.95</mn><mo>×</mo><msup><mn>10</mn><mrow><mi>−</mi><mn>6</mn></mrow></msup></mrow><annotation encoding="application/x-tex">1.95\times10^{-6}</annotation></semantics></math></td>
</tr>
</tbody>
</table></div>
<figure data-latex-placement="H">
<a href="/assets/cae-mcp/force_energy.png" target="_blank" rel="noopener" aria-label="查看force_energy原图"><img src="/assets/cae-mcp/force_energy.png" width="1980" height="836" loading="lazy" decoding="async" alt="产品组独立提取的驱动力与能量 history" /></a>
<figcaption>从产品组新 ODB 独立提取的驱动力与能量 history，保留原始样本。静力步的时间轴是载荷路径参数，不代表已经指定了实际插入速度。</figcaption>
</figure>
<p>所选末帧能量项为 ALLWK 约 3.4821 Nmm、ALLSE 约 1.5564 Nmm、ALLPD 约 0.2456 Nmm、ALLFD 约 1.6753 Nmm。外功减去后三项的可见余额约占 ALLWK 的 0.138%，只用于这些已储存量的核对，不冒充完整能量审计。</p>
<p>PVD 使用 0–107 的顺序索引，因为两个分析步在边界的时间值可能重复。原始步名、帧值和物理总时间仍保存在 manifest 与数据中，序列索引 107 不能被解释为 107 秒。若导出坐标已施加位移，ParaView 不再做第二次 Warp。</p>
<h2 id="三组独立实测都完成了差别在哪里">三组独立实测：都完成了，差别在哪里</h2>
<p>我使用同一输入、同一工程要求和相同算力上限，分别运行三个独立会话。每组都必须产生新的 ODB，允许读供应商文档、自写脚本和调用相同的独立 C++ 转换器。组间不共享脚本、历史解答或计算结果；实际求解串行执行，没有人为设置总时限。</p>
<div class="table-scroll" role="region" tabindex="0" aria-label="数据表，可横向滚动"><table>
<caption>对照设置。A、B 使用相同模型与推理设置，C 同时改变了模型和客户端宿主。</caption>
<thead>
<tr>
<th style="text-align: left;">组别</th>
<th style="text-align: left;">工具条件</th>
<th style="text-align: left;">需要区分的因素</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">A</td>
<td style="text-align: left;">三个 CAE MCP 与工程规程</td>
<td style="text-align: left;">必须产生真实 MCP 调用和新求解产物。</td>
</tr>
<tr>
<td style="text-align: left;">B</td>
<td style="text-align: left;">原生文件与终端工具</td>
<td style="text-align: left;">可自行编写原生脚本；未调用 CAE MCP，使用过通用规划规程。</td>
</tr>
<tr>
<td style="text-align: left;">C</td>
<td style="text-align: left;">原生文件与终端工具</td>
<td style="text-align: left;">使用不同模型与宿主；不能把时间差归因于单一工具因素。</td>
</tr>
</tbody>
</table></div>
<p>评估器重新打开各组的新 ODB，读取控制位移、反力、能量和积分点结果，并检查原生成功标记、网格、VTK 和图片。100 分是本案例产物检查单：输入保护 5、模型定义保留 10、完整新求解 25、控制位移 15、反力与能量核对 10、原生前处理 10、108 帧及区域平均 10、图与曲线 5、资源记录和 datacheck 10。它不是总体成功率，也不是设计验证得分。</p>
<div class="table-scroll" role="region" tabindex="0" aria-label="数据表，可横向滚动"><table>
<caption>工程任务会话的实测结果，每组一次</caption>
<thead>
<tr>
<th style="text-align: left;">组别</th>
<th style="text-align: right;">检查单</th>
<th style="text-align: right;">耗时（min）</th>
<th style="text-align: right;">工具调用</th>
<th style="text-align: right;">MCP 调用</th>
<th style="text-align: right;">峰值（N）</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">A</td>
<td style="text-align: right;">100/100</td>
<td style="text-align: right;">21.82</td>
<td style="text-align: right;">109</td>
<td style="text-align: right;">47</td>
<td style="text-align: right;">1.434141</td>
</tr>
<tr>
<td style="text-align: left;">B</td>
<td style="text-align: right;">100/100</td>
<td style="text-align: right;">27.24</td>
<td style="text-align: right;">81</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">1.434141</td>
</tr>
<tr>
<td style="text-align: left;">C</td>
<td style="text-align: right;">100/100</td>
<td style="text-align: right;">56.13</td>
<td style="text-align: right;">243</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">1.434150</td>
</tr>
</tbody>
</table></div>
<p>A 相对 B 的本次客户端墙钟时间减少约 19.9%。拆开看，三组最终原生分析分别为 647、700、637 秒；剩余任务时间分别约为 662、935、2731 秒，包含输入准备、检查、排错、后处理、网络与等待，不能称为纯模型推理时间。观察到的差异主要发生在工程组织环节，不能写成求解器提速。</p>
<figure data-latex-placement="H">
<a href="/assets/cae-mcp/task_effort.png" target="_blank" rel="noopener" aria-label="查看task_effort原图"><img src="/assets/cae-mcp/task_effort.png" width="1980" height="1540" loading="lazy" decoding="async" alt="三组工程任务耗时、token 与工具调用统计" /></a>
<figcaption>仅统计工程任务会话：耗时、普通输入与输出 token、缓存读取、工具调用。A 为 MCP 与工程规程，B、C 为原生工具组；三者均完成任务。</figcaption>
</figure>
<div class="table-scroll" role="region" tabindex="0" aria-label="数据表，可横向滚动"><table>
<caption>客户端报告的累计 token，普通输入与缓存读取分开列出</caption>
<thead>
<tr>
<th style="text-align: left;">组别</th>
<th style="text-align: right;">普通输入</th>
<th style="text-align: right;">缓存读取</th>
<th style="text-align: right;">输出</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">A</td>
<td style="text-align: right;">119970</td>
<td style="text-align: right;">5048320</td>
<td style="text-align: right;">22840</td>
</tr>
<tr>
<td style="text-align: left;">B</td>
<td style="text-align: right;">121289</td>
<td style="text-align: right;">3867776</td>
<td style="text-align: right;">35711</td>
</tr>
<tr>
<td style="text-align: left;">C</td>
<td style="text-align: right;">132141</td>
<td style="text-align: right;">47289728</td>
<td style="text-align: right;">242125</td>
</tr>
</tbody>
</table></div>
<p>这些数字累计包含每轮重复携带的上下文，不是唯一 query 长度。不同客户端的 input 字段可能包含或不包含缓存，需要拆分后比较；推理 token 若属于输出子集，也不能重复相加。跨供应商 tokenizer 和路由计数没有独立校准，因此这里不推导等价算力或账单。</p>
<p>统计窗口从各组提交共同工程任务到完成并退出，只读取对应任务客户端的最终 usage。报告写作、LaTeX 编译、Tavotto 制图、实验搭建、独立评估、展示视角整理和本次博客发布全部排除。</p>
<h3 id="排错轨迹比一个总分更有信息">排错轨迹比一个总分更有信息</h3>
<p>A 组通过结构化检查和一次有依据的输入修复完成计算。B 组自行组织原生脚本，也完成同样的交付。C 组在接触与耦合关键字布局上反复构建诊断输入，最终通过 CAE 导入、重新导出规范化关键字后完成。</p>
<p>三组保留的含错误 datacheck 数据文件分别为 1、1、15 个。这是不同诊断文件的数量，不是 15 次完整求解失败。原任务限制最多两次有依据的失败修改，原生组实际做了更多输入诊断尝试；这一过程偏离保留说明，没有被 100 分产物检查单覆盖。</p>
<figure data-latex-placement="H">
<a href="/assets/cae-mcp/consistency.png" target="_blank" rel="noopener" aria-label="查看consistency原图"><img src="/assets/cae-mcp/consistency.png" width="1980" height="814" loading="lazy" decoding="async" alt="三组驱动力曲线和相对于数值参考的曲线差异" /></a>
<figcaption>独立提取的三组插入力曲线与参考数值解的差异。接近重合说明同一模型、同一工况的数值一致性；参考解不是试验真值。</figcaption>
</figure>
<p>C 的峰值与数值参考差异约 0.000623%，全曲线归一化 RMSE 约 0.000656%。三组都能完成专业任务，这使比较更关注完成路径、上下文增长和错误恢复。一个案例、每组一次、MCP 与 Skill 同时启用，仍不足以建立普遍能力排序或独立因果结论。</p>
<h2 id="完成计算以后仍需保留哪些工程事实">完成计算以后，仍需保留哪些工程事实</h2>
<p>产品组原生文件包含 6 条 dat 警告、73 条 msg 警告，其中 23 条为负特征值提示，618 个单元被标记为畸变。C 组规范化输入的检查上下文报告了 620 个畸变单元，不能据此声称网格质量改善。</p>
<p>接触非线性中的负特征值可能伴随切线刚度变化，但“最终收敛”不能排除失稳或约束问题。畸变、材料定义、接触区域及网格敏感性仍影响结果的物理可信度。因此本文证明的是给定模型和已确认工况下的工具执行、结果提取与可追溯交付；没有把这次计算扩展为试验相关性、寿命或完整插拔滞回的验证，也没有声称已获得行业公司的认可。</p>
<h2 id="输入query-与可复核资料">输入、query 与可复核资料</h2>
<p>实际输入 INP 为 3,460,015 字节，HM 为 2,313,685 字节。各自 SHA256 随数据中的 provenance 文件提供，用于识别本次实测输入；本文公开测量统计、曲线、可移植 query、LaTeX 与可编辑 Tavotto 图源，工程模型和大体积计算文件不随文发布。</p>
<p>下面是原始任务的可移植整理版摘要，替换了本机绝对路径并省略实验目录隔离措辞，工程条件保持一致。完整整理版与原始 query 指纹随附。</p>
<blockquote>
<p>检查 terminal_pair.hm 与 terminal_pair.inp，保留已有网格、材料、截面和八对接触。按已确认集合固定 male 与 shield 根部，建立 female 和 plate 控制点耦合。Prepress：plate 沿全局 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>+</mi><mi>Y</mi></mrow><annotation encoding="application/x-tex">+Y</annotation></semantics></math> 位移 0.3348 mm；Insertion：保持预压，plate 与 female 同时沿全局 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>−</mi><mi>Z</mi></mrow><annotation encoding="application/x-tex">-Z</annotation></semantics></math> 位移 10 mm。摩擦 0.13，硬接触、有限滑移、NLGEOM，仅两步。以最多 2 CPU、15% 内存上限记录资源选择，运行 datacheck 后提交新求解。读取真实 RP 位移与反力、能量和原积分点应力；转换全部步骤和 108 帧，按 section assignment 做 Avg 75，在 ParaView 核对并输出终点云图、状态文件及驱动力曲线。遇到错误保留原生日志和新输入差异，不修改物理条件来强行收敛。</p>
</blockquote>
<h2 id="实现所依据的原生接口">实现所依据的原生接口</h2>
<p>ODB bulk data 访问、结果平均区域以及作业执行参数均对应供应商文档。工具对这些规则的实现范围已在相应章节说明。</p>
<ul>
<li><p><a href="https://docs.software.vt.edu/abaqusv2025/English/SIMACAECMDRefMap/simacmd-c-odbintrobulkdatacpp.htm">Abaqus：C++ bulk data 访问接口</a>。</p></li>
<li><p><a href="https://docs.software.vt.edu/abaqusv2025/English/SIMACAECAERefMap/simacae-c-resconceptaverage.htm">Abaqus/CAE：结果平均与区域定义</a>。</p></li>
<li><p><a href="https://docs.software.vt.edu/abaqusv2025/English/SIMACAEEXCRefMap/simaexc-c-analysisproc.htm">Abaqus：分析作业执行参数</a>。</p></li>
<li><p><a href="https://modelcontextprotocol.io/">Model Context Protocol</a>。</p></li>
</ul>
<p class="article-downloads"><a href="/assets/cae-mcp/cae-mcp.pdf">PDF 阅读</a> · <a href="/assets/cae-mcp/cae-mcp-sources.zip">LaTeX / Tavotto 图源与数据</a> · <a href="/assets/cae-mcp/engineering-query.txt">完整 query 整理版</a> · <a href="/assets/cae-mcp/task_metrics.csv">实测统计 CSV</a></p></article>
