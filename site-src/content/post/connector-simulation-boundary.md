---
title: "把一次连接器仿真，变成可追溯的批量边界搜索"
date: 2026-10-18
slug: "connector-simulation-boundary"
author: "AlexanderChan"
description: "从子结构降阶、随机公差到并行求解与偏位/偏角边界：一份匿名公开的工程方法记录。LaTeX PDF 正文，Tavotto 方法配图。"
categories: ["Engineering"]
tags: ["FEM", "Automation", "Uncertainty", "LaTeX"]
connector_article: true
---
<article class="cae-article">
<p class="article-downloads"><a href="/articles/connector-simulation/connector-simulation.pdf">中文 PDF</a> · <a href="/articles/connector-simulation/connector-simulation.en.pdf">English PDF</a> · <a href="/articles/connector-simulation/connector-simulation-sources-bilingual.zip">中英文 LaTeX 与配图源文件</a></p><nav class="article-toc" aria-label="文章目录"><details><summary>文章目录</summary><ol><li><a href="#先说收获">先说收获</a></li><li><a href="#问题不再是一个模型而是一族模型">问题不再是一个模型，而是一族模型</a></li><li><a href="#先把重复计算的部分缩小子结构">先把重复计算的部分缩小：子结构</a></li><li><a href="#参数化从一次-gui-操作开始">参数化从一次 GUI 操作开始</a></li><li><a href="#四种抽样共用一个有界概率映射">四种抽样，共用一个有界概率映射</a></li><li><a href="#接口是最容易被自动化放大的建模问题">接口是最容易被自动化放大的建模问题</a></li><li><a href="#把一次运行拆成可恢复的流水线">把一次运行拆成可恢复的流水线</a></li><li><a href="#接触性能先把指标定义清楚">接触性能：先把指标定义清楚</a></li><li><a href="#寻找应用边界而不只是最差样本">寻找应用边界，而不只是最差样本</a></li><li><a href="#我最终会怎样验收这样一套系统">我最终会怎样验收这样一套系统</a></li><li><a href="#结语把可解释性写进自动化">结语：把可解释性写进自动化</a></li><li><a href="#复现与公开资料">复现与公开资料</a></li></ol></details></nav><blockquote>
<p><strong>这篇文章讨论什么？</strong>连接器有限元分析的难点，不只是把一个模型算出来，而是让同一套物理模型能够可靠地产生很多样本，并解释这些样本何时失去接触性能。这里记录一条贯通降阶、参数化、调度、后处理和边界搜索的工程路线。</p>
<p><strong>公开范围。</strong>本文匿名化客户、产品和工况细节，不包含实际模型、原始公差向量、未公开接触力数据或性能指标。抽样图是独立生成的方法演示，其余配图均为示意。新增加的耦合搜索已完成离线代码与坐标检查；实际失效边界仍必须由匹配模型的完整求解确认。</p>
</blockquote>
<h2 class="unnumbered" id="先说收获">先说收获</h2>
<p>一个可用的批量仿真系统，需要把三件事情分别做好：<strong>物理上能解释，数值上能检查，执行上能恢复。</strong>减少求解时间只是第一步；如果每个样本使用了不同的接触设置、施加公差时污染了基准模型，或者把一次求解中断当作失效，那么算得再快也无法得到可信的应用边界。</p>
<p>这条路线可以概括为图 <a href="#fig-workflow">1</a>：用子结构降低重复计算成本，用明确的变量映射生成样本，再用统一的接触指标连接批量统计与姿态搜索。后面的每一步，都保留前面输入的身份与来源。</p>
<figure data-latex-placement="H" id="fig-workflow">
<a href="/articles/connector-simulation/fig01_workflow.png" rel="noopener" target="_blank"><img alt="整体技术路线示意。每个样本沿同一条链路执行；搜索改变的是初始姿态，制造公差组合可以固定。图中没有实际产品模型或性能数据。" decoding="async" loading="lazy" src="/articles/connector-simulation/fig01_workflow.png" style="width:100%;height:auto"/></a>
<figcaption>整体技术路线示意。每个样本沿同一条链路执行；搜索改变的是初始姿态，制造公差组合可以固定。图中没有实际产品模型或性能数据。</figcaption>
</figure>
<h2 id="问题不再是一个模型而是一族模型">问题不再是一个模型，而是一族模型</h2>
<p>连接器互配是典型的接触非线性问题：几何、局部刚度、初始间隙和加载过程共同影响最终接触状态。名义几何上的一次计算，只回答了某个确定配置的问题。引入制造偏差后，需要研究一族模型的响应；进一步考虑装配偏位和偏角，又增加了新的条件变量。</p>
<p>我把这一问题写成 <math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi mathvariant="bold-italic">𝒚</mi><mo>=</mo><mi mathvariant="script">𝒮</mi><mo form="prefix" stretchy="false">(</mo><mi mathvariant="bold-italic">𝝃</mi><mo>,</mo><mi mathvariant="bold-italic">𝒒</mi><mo>;</mo><mi mathvariant="bold-italic">𝜼</mi><mo form="postfix" stretchy="false">)</mo><mo>,</mo></mrow><annotation encoding="application/x-tex">\begin{equation}
 \mathbf{y}=\mathcal{S}(\boldsymbol{\xi},\mathbf{q};\boldsymbol{\eta}),
\end{equation}</annotation></semantics></math> 其中 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi mathvariant="bold-italic">𝝃</mi><annotation encoding="application/x-tex">\boldsymbol{\xi}</annotation></semantics></math> 是制造公差向量，<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi mathvariant="bold-italic">𝒒</mi><annotation encoding="application/x-tex">\mathbf{q}</annotation></semantics></math> 是初始装配姿态，<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi mathvariant="bold-italic">𝜼</mi><annotation encoding="application/x-tex">\boldsymbol{\eta}</annotation></semantics></math> 是材料、摩擦、预压和插入路径等物理设置，<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi mathvariant="script">𝒮</mi><annotation encoding="application/x-tex">\mathcal{S}</annotation></semantics></math> 表示有限元建模、装配与求解流程，<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi mathvariant="bold-italic">𝒚</mi><annotation encoding="application/x-tex">\mathbf{y}</annotation></semantics></math> 则包含接触力曲线及其终点指标。</p>
<p>这个写法首先提醒我们：<strong>制造公差不是装配姿态，抽样策略也不是物理设置。</strong>比较采样方法时，应保持后两者一致；搜索姿态边界时，则应固定同一条制造公差向量。否则，曲线的变化无法归因。</p>
<p>项目的工作由此自然分成两层。第一层是让确定性分析足够高效，为批量运行提供底座；第二层是在同一底座上引入公差，并建立失效边界的自动搜索。本文重点是两层之间的工程连接，而不是额外引入一个预测模型。</p>
<h2 id="先把重复计算的部分缩小子结构">先把重复计算的部分缩小：子结构</h2>
<h3 id="core-和-sub-到底指什么">CORE 和 SUB 到底指什么</h3>
<p>有限元方法（Finite Element Method，FEM）将连续体离散成节点和单元。本文把需要保留细节的非线性接触区域称为 <strong>CORE（核心保留区）</strong>，把适合凝聚处理的部分称为 <strong>SUB（子结构区）</strong>。它们是工程分区名称，不是求解器的材料类型或特定单元名称。</p>
<p>图 <a href="#fig-sub">2</a> 用抽象网格解释这种分区：接触和局部变形集中在 CORE，远离关键接触的结构通过保留接口节点传递载荷。划分不能仅凭单元数；需要考虑接触是否会进入子结构区域、材料非线性是否重要，以及接口是否保留了正确的运动自由度。</p>
<figure data-latex-placement="H" id="fig-sub">
<a href="/articles/connector-simulation/fig02_substructure.png" rel="noopener" target="_blank"><img alt="子结构分区与凝聚示意。左侧为完整网格，右侧为保留接口与核心细节后的使用层模型。圆点表示接口自由度，矩形不代表实际连接器几何。" decoding="async" loading="lazy" src="/articles/connector-simulation/fig02_substructure.png" style="width:100%;height:auto"/></a>
<figcaption>子结构分区与凝聚示意。左侧为完整网格，右侧为保留接口与核心细节后的使用层模型。圆点表示接口自由度，矩形不代表实际连接器几何。</figcaption>
</figure>
<h3 id="静力凝聚为什么能减少重复工作">静力凝聚为什么能减少重复工作</h3>
<p>将线性子结构的自由度分为内部自由度 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>i</mi><annotation encoding="application/x-tex">i</annotation></semantics></math> 与保留自由度 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>b</mi><annotation encoding="application/x-tex">b</annotation></semantics></math>，其方程可以写为 <math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mrow><mo form="prefix" stretchy="true">[</mo><mtable><mtr><mtd columnalign="center" style="text-align: center"><msub><mi>K</mi><mrow><mi>i</mi><mi>i</mi></mrow></msub></mtd><mtd columnalign="center" style="text-align: center"><msub><mi>K</mi><mrow><mi>i</mi><mi>b</mi></mrow></msub></mtd></mtr><mtr><mtd columnalign="center" style="text-align: center"><msub><mi>K</mi><mrow><mi>b</mi><mi>i</mi></mrow></msub></mtd><mtd columnalign="center" style="text-align: center"><msub><mi>K</mi><mrow><mi>b</mi><mi>b</mi></mrow></msub></mtd></mtr></mtable><mo form="postfix" stretchy="true">]</mo></mrow><mrow><mo form="prefix" stretchy="true">[</mo><mtable><mtr><mtd columnalign="center" style="text-align: center"><msub><mi>u</mi><mi>i</mi></msub></mtd></mtr><mtr><mtd columnalign="center" style="text-align: center"><msub><mi>u</mi><mi>b</mi></msub></mtd></mtr></mtable><mo form="postfix" stretchy="true">]</mo></mrow><mo>=</mo><mrow><mo form="prefix" stretchy="true">[</mo><mtable><mtr><mtd columnalign="center" style="text-align: center"><msub><mi>f</mi><mi>i</mi></msub></mtd></mtr><mtr><mtd columnalign="center" style="text-align: center"><msub><mi>f</mi><mi>b</mi></msub></mtd></mtr></mtable><mo form="postfix" stretchy="true">]</mo></mrow><mi>.</mi></mrow><annotation encoding="application/x-tex">\begin{equation}
 \begin{bmatrix}K_{ii}&amp;K_{ib}\\K_{bi}&amp;K_{bb}\end{bmatrix}
 \begin{bmatrix}u_i\\u_b\end{bmatrix}
 =\begin{bmatrix}f_i\\f_b\end{bmatrix}.
\end{equation}</annotation></semantics></math> 消去内部自由度后，可得约化关系 <math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mtable><mtr><mtd columnalign="right" style="text-align: right; padding-right: 0"><msub><mover><mi>K</mi><mo accent="true">¯</mo></mover><mrow><mi>b</mi><mi>b</mi></mrow></msub></mtd><mtd columnalign="left" style="text-align: left; padding-left: 0"><mo>=</mo><msub><mi>K</mi><mrow><mi>b</mi><mi>b</mi></mrow></msub><mo>−</mo><msub><mi>K</mi><mrow><mi>b</mi><mi>i</mi></mrow></msub><msubsup><mi>K</mi><mrow><mi>i</mi><mi>i</mi></mrow><mrow><mi>−</mi><mn>1</mn></mrow></msubsup><msub><mi>K</mi><mrow><mi>i</mi><mi>b</mi></mrow></msub><mo>,</mo></mtd></mtr><mtr><mtd columnalign="right" style="text-align: right; padding-right: 0"><msub><mover><mi>f</mi><mo accent="true">¯</mo></mover><mi>b</mi></msub></mtd><mtd columnalign="left" style="text-align: left; padding-left: 0"><mo>=</mo><msub><mi>f</mi><mi>b</mi></msub><mo>−</mo><msub><mi>K</mi><mrow><mi>b</mi><mi>i</mi></mrow></msub><msubsup><mi>K</mi><mrow><mi>i</mi><mi>i</mi></mrow><mrow><mi>−</mi><mn>1</mn></mrow></msubsup><msub><mi>f</mi><mi>i</mi></msub><mo>,</mo><mspace width="2.0em"></mspace><msub><mover><mi>K</mi><mo accent="true">¯</mo></mover><mrow><mi>b</mi><mi>b</mi></mrow></msub><msub><mi>u</mi><mi>b</mi></msub><mo>=</mo><msub><mover><mi>f</mi><mo accent="true">¯</mo></mover><mi>b</mi></msub><mi>.</mi></mtd></mtr></mtable><annotation encoding="application/x-tex">\begin{align}
 \overline K_{bb}&amp;=K_{bb}-K_{bi}K_{ii}^{-1}K_{ib},\\
 \overline f_b&amp;=f_b-K_{bi}K_{ii}^{-1}f_i,\qquad
 \overline K_{bb}u_b=\overline f_b.
\end{align}</annotation></semantics></math> 这里的逆矩阵是数学表达，实际计算通常通过线性方程求解实现，并不需要显式形成整个逆矩阵。子结构生成阶段承担约化工作；使用阶段则把约化库与 CORE 装配起来。</p>
<p>收益来自复用，而不是简单地把模型中一片区域删除。如果多个样本只改变 CORE，且子结构本身与接口定义仍适用，就可以复用同一套库。反之，若子结构几何、材料、保留自由度或生成工况发生变化，就不能只因为文件名相同而继续使用旧库。</p>
<h3 id="文件是一套不是一堆">文件是一套，不是一堆</h3>
<p>输入文件（input deck，通常为 <code>.inp</code>）记录网格、集合与关键字。子结构相关的仿真数据库 <code>.sim</code>、子结构库 <code>.sup</code> 和输出数据库（Output Database，ODB，<code>.odb</code>）是不同用途的产物，不应仅凭扩展名逐个替换。它们必须来自匹配的生成任务，并与接口节点标签一致。</p>
<p>因此，我把“库的来源”也当成输入：记录生成文件、保留集合、模型身份和校验结果。批量装配时按标签建立接口集合，而不是在大模型中临时猜测最近的坐标点。子结构方法的基本原则可参见 Abaqus 官方文档 <a href="#ref-abaqus-sub">[1]</a>；具体适用性仍要由当前模型验证。</p>
<h2 id="参数化从一次-gui-操作开始">参数化从一次 GUI 操作开始</h2>
<h3 id="先录下能成功的操作再封装">先录下能成功的操作，再封装</h3>
<p>图形用户界面（Graphical User Interface，GUI）中的一次正确操作，是自动化最可靠的起点之一。HyperMesh 的命令历史保存了对应的工具命令语言（Tool Command Language，Tcl）指令。我的做法是先在 GUI 中完成目标动作，再从历史中提取必要命令，而不是根据面板名称猜 API 参数。</p>
<p>清洗历史时，会删除视角、选择面板等与物理结果无关的动作，保留明确的实体选择、shape 施加与导出步骤，再把路径、幅值和输出名称变成函数参数。Python 负责样本、文件和进程管理，Tcl 负责在 HyperMesh 内执行已有能力。Notebook 只是交互入口，实际逻辑仍放在可被命令行调用的 Python 模块中。</p>
<p>应用程序编程接口（Application Programming Interface，API）在不同软件版本之间可能存在差异。由此得到的教训是：以安装版本和录制命令为依据，不把“新版本文档里有这个函数”当作旧版本可运行的保证。</p>
<h3 id="shape-幅值不是毫米">shape 幅值不是毫米</h3>
<p>网格形变（mesh morphing）可以把已定义的形状扰动（shape）参数化。对存为节点扰动的 shape，一种清楚的表达是 <math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi mathvariant="bold-italic">𝒙</mi><mo form="prefix" stretchy="false">(</mo><mi mathvariant="bold-italic">𝜶</mi><mo form="postfix" stretchy="false">)</mo><mo>=</mo><msub><mi mathvariant="bold-italic">𝒙</mi><mn>0</mn></msub><mo>+</mo><munderover><mo>∑</mo><mrow><mi>j</mi><mo>=</mo><mn>1</mn></mrow><msub><mi>d</mi><mi>g</mi></msub></munderover><msub><mi>α</mi><mi>j</mi></msub><mspace width="0.167em"></mspace><mi mathvariant="normal">Δ</mi><msub><mi mathvariant="bold-italic">𝒙</mi><mi>j</mi></msub><mo>,</mo></mrow><annotation encoding="application/x-tex">\begin{equation}
 \mathbf{x}(\boldsymbol{\alpha})=\mathbf{x}_0+
 \sum_{j=1}^{d_g}\alpha_j\,\Delta\mathbf{x}_j,
\end{equation}</annotation></semantics></math> 其中 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>α</mi><mi>j</mi></msub><annotation encoding="application/x-tex">\alpha_j</annotation></semantics></math> 是无量纲幅值，<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi mathvariant="normal">Δ</mi><msub><mi mathvariant="bold-italic">𝒙</mi><mi>j</mi></msub></mrow><annotation encoding="application/x-tex">\Delta\mathbf{x}_j</annotation></semantics></math> 是基准模型中保存的节点位移场。若幅值为 1 对应特征尺寸变化 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>s</mi><mi>j</mi></msub><annotation encoding="application/x-tex">s_j</annotation></semantics></math>，则该特征的尺寸变化为 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi mathvariant="normal">Δ</mi><msub><mi>L</mi><mi>j</mi></msub><mo>=</mo><msub><mi>s</mi><mi>j</mi></msub><msub><mi>α</mi><mi>j</mi></msub></mrow><annotation encoding="application/x-tex">\Delta L_j=s_j\alpha_j</annotation></semantics></math>。方向、单位、标定尺度和 shape 名称必须共同记录。</p>
<p>这也是为什么我更重视“节点扰动保存了什么”，而不仅是 GUI 中输入了多少。依赖 handle、morph volume 或约束更新的 shape，可能涉及额外的重算语义。对需要稳定叠加的参数，应检查保存形式，独立施加与组合施加的结果，并用坐标验证确认期望的位移场。上面的叠加式只描述明确保存的节点扰动，不应被理解成所有交互式 morph 操作都线性、可交换。</p>
<h3 id="一份向量可以包含不同类型的公差">一份向量可以包含不同类型的公差</h3>
<p>除几何 shape 外，参数还可以作用于不同部件的预抬量或局部位置。于是输入向量可以分组： <math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi mathvariant="bold-italic">𝝃</mi><mo>=</mo><mo form="prefix" maxsize="120%" minsize="120%" stretchy="true">[</mo><msub><mi mathvariant="bold-italic">𝜶</mi><mrow><mi mathvariant="normal">s</mi><mi mathvariant="normal">h</mi><mi mathvariant="normal">a</mi><mi mathvariant="normal">p</mi><mi mathvariant="normal">e</mi></mrow></msub><mo>,</mo><mspace width="0.278em"></mspace><msub><mi mathvariant="bold-italic">𝜶</mi><mrow><mi mathvariant="normal">p</mi><mi mathvariant="normal">r</mi><mi mathvariant="normal">e</mi><mi mathvariant="normal">l</mi><mi mathvariant="normal">i</mi><mi mathvariant="normal">f</mi><mi mathvariant="normal">t</mi></mrow></msub><mo>,</mo><mspace width="0.278em"></mspace><msub><mi mathvariant="bold-italic">𝜶</mi><mrow><mi mathvariant="normal">l</mi><mi mathvariant="normal">o</mi><mi mathvariant="normal">c</mi><mi mathvariant="normal">a</mi><mi mathvariant="normal">l</mi><mspace width="0.222em"></mspace><mi mathvariant="normal">o</mi><mi mathvariant="normal">f</mi><mi mathvariant="normal">f</mi><mi mathvariant="normal">s</mi><mi mathvariant="normal">e</mi><mi mathvariant="normal">t</mi></mrow></msub><mo form="postfix" maxsize="120%" minsize="120%" stretchy="true">]</mo><mi>.</mi></mrow><annotation encoding="application/x-tex">\begin{equation}
 \boldsymbol{\xi}=\bigl[\boldsymbol{\alpha}_{\mathrm{shape}},\;
 \boldsymbol{\alpha}_{\mathrm{prelift}},\;
 \boldsymbol{\alpha}_{\mathrm{local\ offset}}\bigr].
\end{equation}</annotation></semantics></math> 几何组映射到节点，预抬组映射到独立控制点与加载边界，局部偏移组映射到明确部件的坐标。让所有组共用一份记录，不等于让所有组都必须通过 morph 实现。这样既能保留同一向量的可追溯性，又避免为简单刚体平移制造复杂的形变操作。</p>
<h2 id="四种抽样共用一个有界概率映射">四种抽样，共用一个有界概率映射</h2>
<h3 id="为什么先定义分布再谈抽样">为什么先定义分布，再谈抽样</h3>
<p>普通正态分布没有有限上下界。如果工程上规定幅值只能位于 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo form="prefix" stretchy="false">[</mo><mi>−</mi><mn>1</mn><mo>,</mo><mn>1</mn><mo form="postfix" stretchy="false">]</mo></mrow><annotation encoding="application/x-tex">[-1,1]</annotation></semantics></math>，就不能一边使用不截断正态抽样，一边假设结果一定不会越界。直接把超界值裁到端点也不等价：裁剪会在上下界形成点质量，改变分布形态。</p>
<p>本流程采用条件截断正态。令 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi mathvariant="normal">Φ</mi><annotation encoding="application/x-tex">\Phi</annotation></semantics></math>、<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>ϕ</mi><annotation encoding="application/x-tex">\phi</annotation></semantics></math> 为标准正态分布的累积分布函数与密度，<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>u</mi><mo>∈</mo><mo form="prefix" stretchy="false">(</mo><mn>0</mn><mo>,</mo><mn>1</mn><mo form="postfix" stretchy="false">)</mo></mrow><annotation encoding="application/x-tex">u\in(0,1)</annotation></semantics></math>，则 <math display="block" id="eq-inverse" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>α</mi><mo>=</mo><mi>μ</mi><mo>+</mo><mi>σ</mi><msup><mi mathvariant="normal">Φ</mi><mrow><mi>−</mi><mn>1</mn></mrow></msup><mspace width="-0.167em"></mspace><mrow><mo form="prefix" stretchy="true">[</mo><mi mathvariant="normal">Φ</mi><mspace width="-0.167em"></mspace><mrow><mo form="prefix" stretchy="true">(</mo><mfrac><mrow><mi>a</mi><mo>−</mo><mi>μ</mi></mrow><mi>σ</mi></mfrac><mo form="postfix" stretchy="true">)</mo></mrow><mo>+</mo><mi>u</mi><mrow><mo form="prefix" stretchy="true">{</mo><mi mathvariant="normal">Φ</mi><mspace width="-0.167em"></mspace><mrow><mo form="prefix" stretchy="true">(</mo><mfrac><mrow><mi>b</mi><mo>−</mo><mi>μ</mi></mrow><mi>σ</mi></mfrac><mo form="postfix" stretchy="true">)</mo></mrow><mo>−</mo><mi mathvariant="normal">Φ</mi><mspace width="-0.167em"></mspace><mrow><mo form="prefix" stretchy="true">(</mo><mfrac><mrow><mi>a</mi><mo>−</mo><mi>μ</mi></mrow><mi>σ</mi></mfrac><mo form="postfix" stretchy="true">)</mo></mrow><mo form="postfix" stretchy="true">}</mo></mrow><mo form="postfix" stretchy="true">]</mo></mrow><mo>,</mo><mspace width="1.0em"></mspace><mi>a</mi><mo>=</mo><mi>−</mi><mn>1</mn><mo>,</mo><mspace width="0.278em"></mspace><mi>b</mi><mo>=</mo><mn>1</mn><mi>.</mi></mrow><annotation encoding="application/x-tex">\begin{equation}
\label{eq:inverse}
 \alpha=\mu+\sigma\Phi^{-1}\!\left[
 \Phi\!\left(\frac{a-\mu}{\sigma}\right)+u
 \left\{\Phi\!\left(\frac{b-\mu}{\sigma}\right)
 -\Phi\!\left(\frac{a-\mu}{\sigma}\right)\right\}\right],
 \quad a=-1,\;b=1.
\end{equation}</annotation></semantics></math> 四种方法首先产生单位超立方体中的点，再共同使用式 <a href="#eq-inverse">(7)</a> 映射到各变量的幅值。这样，“怎样布点”和“变量服从什么分布”便被分开了。</p>
<p>需要特别区分：<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>μ</mi><annotation encoding="application/x-tex">\mu</annotation></semantics></math> 和 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>σ</mi><annotation encoding="application/x-tex">\sigma</annotation></semantics></math> 是<strong>截断前母分布</strong>的参数。截断后，尤其截断范围较窄时，实际样本标准差不会仍然等于 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>σ</mi><annotation encoding="application/x-tex">\sigma</annotation></semantics></math>。即使各维使用相同映射，也不自动代表工程上已证明各变量互相独立；缺少相关性数据时，独立只是一个需要明确写出的建模假设。</p>
<h3 id="四种方法各解决什么问题">四种方法各解决什么问题</h3>
<p><strong>蒙特卡洛（Monte Carlo，MC）</strong>使用独立伪随机点，概念直接，适合作为基准。有限样本中出现局部聚集和空缺是其正常表现，固定随机种子可以重现同一设计。</p>
<p><strong>拉丁超立方抽样（Latin Hypercube Sampling，LHS）</strong>在每一维把概率轴分成等概率区间，每个区间取一个点，再进行维度间配对。它保证单维分层覆盖，但并不保证所有高维组合都均匀，也不自动包含变量之间的真实制造相关性。</p>
<p><strong>Sobol 序列</strong>和<strong>Halton 序列</strong>属于低差异设计，可用于准蒙特卡洛（Quasi-Monte Carlo，QMC）方法。Sobol 常按 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msup><mn>2</mn><mi>m</mi></msup><annotation encoding="application/x-tex">2^m</annotation></semantics></math> 个点生成以保留设计性质；加扰设计有助于避免直接使用固定确定性图样。低维图上看起来整齐，并不能单独证明其在当前高维非线性接触问题上更准确。方法背景参见文献 <a href="#ref-mckay">[3]</a>,<a href="#ref-sobol">[4]</a>,<a href="#ref-halton">[5]</a>,<a href="#ref-scipy-qmc">[6]</a>。</p>
<figure data-latex-placement="H" id="fig-sampling">
<a href="/articles/connector-simulation/fig03_sampling.png" rel="noopener" target="_blank"><img alt="四种方法的独立抽样演示，每种 n = 256 n=256 ，固定种子 20261018。上排是映射前的二维单位方形设计，下排是第一维映射后的幅值直方图；橙线是 N ( 0 , 1 ) N(0,1) 条件截断到 [ − 1 , 1 ] [-1,1] 后的理论密度。此图不是项目原始样本，也不是仿真性能对比。" decoding="async" loading="lazy" src="/articles/connector-simulation/fig03_sampling.png" style="width:100%;height:auto"/></a>
<figcaption>四种方法的独立抽样演示，每种 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>n</mi><mo>=</mo><mn>256</mn></mrow><annotation encoding="application/x-tex">n=256</annotation></semantics></math>，固定种子 20261018。上排是映射前的二维单位方形设计，下排是第一维映射后的幅值直方图；橙线是 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>N</mi><mo form="prefix" stretchy="false">(</mo><mn>0</mn><mo>,</mo><mn>1</mn><mo form="postfix" stretchy="false">)</mo></mrow><annotation encoding="application/x-tex">N(0,1)</annotation></semantics></math> 条件截断到 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo form="prefix" stretchy="false">[</mo><mi>−</mi><mn>1</mn><mo>,</mo><mn>1</mn><mo form="postfix" stretchy="false">]</mo></mrow><annotation encoding="application/x-tex">[-1,1]</annotation></semantics></math> 后的理论密度。此图不是项目原始样本，也不是仿真性能对比。</figcaption>
</figure>
<p>如图 <a href="#fig-sampling">3</a> 所示，布点方法改变的是有限点集的覆盖方式，共用的逆分布映射则使目标边缘分布保持一致。比较方法时，应记录样本数、随机种子或加扰设置、变量次序、上下界、物理换算系数及相关性假设。若要比较估计误差，应进行适当的重复设计与误差分析，而不能只挑一张更平滑的直方图作为证据。</p>
<h2 id="接口是最容易被自动化放大的建模问题">接口是最容易被自动化放大的建模问题</h2>
<h3 id="形变边界不能突然停止">形变边界不能突然停止</h3>
<p>局部区域移动，而紧邻它的网格或约束完全不动时，位移可能集中在很薄的一层单元中。视觉上不一定明显重叠，但单元可能被过度压缩，进而出现雅可比或体积问题。给定一个看似很小的公差，不能替代网格质量检查；真正重要的是相对于局部网格尺寸和过渡长度的变形梯度。</p>
<p>因此，我把关键界面的固定约束、过渡区域和形变后网格检查作为模型定义的一部分。基准无误并不意味着所有极端样本都有效；极端幅值与组合样本应先试算，再扩大批量规模。</p>
<h3 id="局部制造偏移与整体装配偏位不是一回事">局部制造偏移与整体装配偏位不是一回事</h3>
<p>图 <a href="#fig-pose">4</a> 区分了两种表面相似的操作。第一种只移动某根端子的 CORE 部分而子结构不动，属于局部制造偏差的建模选择，会造成接口不共节点。第二种是整套公端相对母端移动，公端 CORE 与其子结构必须同步改变位置；这属于初始装配姿态。</p>
<figure data-latex-placement="H" id="fig-pose">
<a href="/articles/connector-simulation/fig04_pose.png" rel="noopener" target="_blank"><img alt="两种位移的物理含义示意。虚线为原位置，实线为修改后位置；图中位移和角度仅为示意，不按比例。整体装配偏位不应人为增加公端内部接口间隙。" decoding="async" loading="lazy" src="/articles/connector-simulation/fig04_pose.png" style="width:100%;height:auto"/></a>
<figcaption>两种位移的物理含义示意。虚线为原位置，实线为修改后位置；图中位移和角度仅为示意，不按比例。整体装配偏位不应人为增加公端内部接口间隙。</figcaption>
</figure>
<p>对于不共节点接口，可采用绑定约束（Tie constraint）。但增大位置容差，只是改变哪些节点或面可能进入绑定范围，<strong>不是任意几何错位都可被“修好”的理由</strong>。位置调整还可能把已施加的偏差拉回去；关闭调整则需要进一步检查实际绑定覆盖与力学含义。文献 <a href="#ref-abaqus-tie">[2]</a> 对这些行为有明确说明。</p>
<p>代码层的最低要求，是检查对应标签节点的距离、容差是否覆盖，以及装配输入是否保留了预期偏移。最终仍需检查求解器实际建立的约束。用一个极大的统一容差跨越多个邻近端子，会让自动化变得更危险，而不是更稳健。</p>
<h2 id="把一次运行拆成可恢复的流水线">把一次运行拆成可恢复的流水线</h2>
<h3 id="阶段比一个返回码更重要">阶段比一个返回码更重要</h3>
<p>批量求解不是在循环里调用求解器那么简单。我把每个 case（独立工况样本）拆成几个可记录的阶段：</p>
<div class="center">
<p>准备输入 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mo>→</mo><annotation encoding="application/x-tex">\longrightarrow</annotation></semantics></math> 装配 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mo>→</mo><annotation encoding="application/x-tex">\longrightarrow</annotation></semantics></math> 输入检查 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mo>→</mo><annotation encoding="application/x-tex">\longrightarrow</annotation></semantics></math> 求解 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mo>→</mo><annotation encoding="application/x-tex">\longrightarrow</annotation></semantics></math> 后处理。</p>
</div>
<p>输入检查（data check）通过，不代表已经进行了完整求解；外层进程正常结束，也不代表内部求解成功。系统需要同时检查求解日志、锁文件状态和完成标记，再确认 ODB 中存在所需分析步与结果。</p>
<p>每次尝试使用独立的 attempt（运行尝试）目录，避免旧产物被误认为本次成功结果。记录中还应保留输入文件身份、所选公差行、使用的子结构库、软件版本、CPU 和内存设置、阶段耗时以及错误位置。这些元数据往往比一份孤立的结果 CSV 更有价值。</p>
<h3 id="并行数每任务核心数和内存是三个参数">并行数、每任务核心数和内存是三个参数</h3>
<p>中央处理器（Central Processing Unit，CPU）的每任务核心数不等于同时运行的 case 数。若每个作业使用 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>c</mi><annotation encoding="application/x-tex">c</annotation></semantics></math> 核，最多同时运行 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>p</mi><annotation encoding="application/x-tex">p</annotation></semantics></math> 个重计算任务，至少需要满足 <math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>p</mi><mspace width="0.167em"></mspace><mi>c</mi><mo>≤</mo><msub><mi>C</mi><mrow><mi mathvariant="normal">a</mi><mi mathvariant="normal">v</mi><mi mathvariant="normal">a</mi><mi mathvariant="normal">i</mi><mi mathvariant="normal">l</mi><mi mathvariant="normal">a</mi><mi mathvariant="normal">b</mi><mi mathvariant="normal">l</mi><mi mathvariant="normal">e</mi></mrow></msub><mo>,</mo><mspace width="2.0em"></mspace><munder><mo>∑</mo><mrow><mi>k</mi><mo>∈</mo><mi mathvariant="script">𝒜</mi></mrow></munder><msub><mi>M</mi><mi>k</mi></msub><mo>≤</mo><msub><mi>M</mi><mrow><mi mathvariant="normal">b</mi><mi mathvariant="normal">u</mi><mi mathvariant="normal">d</mi><mi mathvariant="normal">g</mi><mi mathvariant="normal">e</mi><mi mathvariant="normal">t</mi></mrow></msub><mo>,</mo></mrow><annotation encoding="application/x-tex">\begin{equation}
 p\,c\le C_{\mathrm{available}},\qquad
 \sum_{k\in\mathcal{A}} M_k\le M_{\mathrm{budget}},
\end{equation}</annotation></semantics></math> 其中 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi mathvariant="script">𝒜</mi><annotation encoding="application/x-tex">\mathcal{A}</annotation></semantics></math> 是活动作业集合，<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>M</mi><mi>k</mi></msub><annotation encoding="application/x-tex">M_k</annotation></semantics></math> 是用于调度评估的任务内存预算。软件的内存百分比是作业配置上限，不是实测峰值，也不是操作系统已经为它预留的物理内存。前处理、后处理、网格导出和文件缓存同样需要余量。</p>
<p>协调器可以用 Python 线程等待外部进程，但真正的有限元计算由多个独立求解器进程完成。为每条搜索路径各建一个大线程池，会导致并行数相乘；更合适的方式是用一条全局队列，分别限制网格导出、子结构生成和整体求解的并发。</p>
<h3 id="恢复不是删除锁文件">恢复不是删除锁文件</h3>
<p>Notebook 内核中断后，外部求解器可能仍在运行。恢复之前必须判断旧任务是否存活，不能仅靠一个状态文件或随手删除 <code>.lck</code> 来决定重复提交。已经完成的样本应复用，失败或未知的样本应有显式重试选项。</p>
<p>同时，配置改变需要分层看待。仅调整调度并发，可以在安全停止后继续使用相同物理结果；如果摩擦、插入终点、制造公差、模型或相关代码的身份改变，就不能把新结果混进旧批次。对输入做哈希并冻结配置，可以把这条原则变成系统检查，而不是依赖操作者记忆。</p>
<h2 id="接触性能先把指标定义清楚">接触性能：先把指标定义清楚</h2>
<p>本文关注的是法向接触性能，而不是把总反力直接当成某一对接触力。对第 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>i</mi><annotation encoding="application/x-tex">i</annotation></semantics></math> 对接触，设求解器输出的总法向接触力向量为 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msubsup><mi mathvariant="bold-italic">𝑭</mi><mi>i</mi><mrow><mi mathvariant="normal">n</mi><mi mathvariant="normal">o</mi><mi mathvariant="normal">r</mi><mi mathvariant="normal">m</mi><mi mathvariant="normal">a</mi><mi mathvariant="normal">l</mi></mrow></msubsup><annotation encoding="application/x-tex">\mathbf{F}^{\mathrm{normal}}_i</annotation></semantics></math>，当前流程取其全局 Y 分量： <math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>F</mi><mi>i</mi></msub><mo form="prefix" stretchy="false">(</mo><mi>u</mi><mo form="postfix" stretchy="false">)</mo><mo>=</mo><mrow><mo form="prefix" stretchy="true">|</mo><msubsup><mi mathvariant="bold-italic">𝑭</mi><mi>i</mi><mrow><mi mathvariant="normal">n</mi><mi mathvariant="normal">o</mi><mi mathvariant="normal">r</mi><mi mathvariant="normal">m</mi><mi mathvariant="normal">a</mi><mi mathvariant="normal">l</mi></mrow></msubsup><mo form="prefix" stretchy="false">(</mo><mi>u</mi><mo form="postfix" stretchy="false">)</mo><mo>⋅</mo><msub><mi mathvariant="bold-italic">𝒆</mi><mi>y</mi></msub><mo form="postfix" stretchy="true">|</mo></mrow><mo>=</mo><mo form="prefix" stretchy="false">|</mo><msub><mrow><mi mathvariant="normal">C</mi><mi mathvariant="normal">F</mi><mi mathvariant="normal">N</mi><mn mathvariant="normal">2</mn></mrow><mi>i</mi></msub><mo form="prefix" stretchy="false">(</mo><mi>u</mi><mo form="postfix" stretchy="false">)</mo><mo form="prefix" stretchy="false">|</mo><mi>.</mi></mrow><annotation encoding="application/x-tex">\begin{equation}
 F_i(u)=\left|\mathbf{F}^{\mathrm{normal}}_i(u)\cdot\mathbf{e}_y\right|
       =|\mathrm{CFN2}_i(u)|.
\end{equation}</annotation></semantics></math> 这里的 <code>CFN2</code> 是法向接触力合力的第二个坐标分量，不是单个节点的接触压力，也不是一般情形下的法向合力模长。初始偏角改变后，必须持续核对全局分量是否仍符合工程指标的定义；不能把分量和向量范数混用。</p>
<p>在指定最终插入位移 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>u</mi><mo>⋆</mo></msub><annotation encoding="application/x-tex">u_\star</annotation></semantics></math> 处，定义 <math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>F</mi><mi mathvariant="normal">min</mi></msub><mo form="prefix" stretchy="false">(</mo><mi mathvariant="bold-italic">𝒒</mi><mo>,</mo><mi mathvariant="bold-italic">𝝃</mi><mo form="postfix" stretchy="false">)</mo><mo>=</mo><munder><mi mathvariant="normal">min</mi><mrow><mn>1</mn><mo>≤</mo><mi>i</mi><mo>≤</mo><msub><mi>n</mi><mi>c</mi></msub></mrow></munder><msub><mi>F</mi><mi>i</mi></msub><mo form="prefix" stretchy="false">(</mo><msub><mi>u</mi><mo>⋆</mo></msub><mo form="postfix" stretchy="false">)</mo><mo>,</mo><mspace width="2.0em"></mspace><mi>g</mi><mo form="prefix" stretchy="false">(</mo><mi mathvariant="bold-italic">𝒒</mi><mo>;</mo><mi mathvariant="bold-italic">𝝃</mi><mo form="postfix" stretchy="false">)</mo><mo>=</mo><msub><mi>F</mi><mi mathvariant="normal">min</mi></msub><mo form="prefix" stretchy="false">(</mo><mi mathvariant="bold-italic">𝒒</mi><mo>,</mo><mi mathvariant="bold-italic">𝝃</mi><mo form="postfix" stretchy="false">)</mo><mo>−</mo><msub><mi>F</mi><mrow><mi mathvariant="normal">c</mi><mi mathvariant="normal">r</mi><mi mathvariant="normal">i</mi><mi mathvariant="normal">t</mi></mrow></msub><mi>.</mi></mrow><annotation encoding="application/x-tex">\begin{equation}
 F_{\min}(\mathbf q,\boldsymbol\xi)=\min_{1\le i\le n_c}F_i(u_\star),\qquad
 g(\mathbf q;\boldsymbol\xi)=F_{\min}(\mathbf q,\boldsymbol\xi)-F_{\mathrm{crit}}.
\end{equation}</annotation></semantics></math> 其中 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>n</mi><mi>c</mi></msub><annotation encoding="application/x-tex">n_c</annotation></semantics></math> 是需要检查的接触对数量，<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><msub><mi>F</mi><mrow><mi mathvariant="normal">c</mi><mi mathvariant="normal">r</mi><mi mathvariant="normal">i</mi><mi mathvariant="normal">t</mi></mrow></msub><annotation encoding="application/x-tex">F_{\mathrm{crit}}</annotation></semantics></math> 是配置中的工程阈值。<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>g</mi><mo>&lt;</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">g&lt;0</annotation></semantics></math> 表示至少一对接触低于阈值；<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>g</mi><mo>≥</mo><mn>0</mn></mrow><annotation encoding="application/x-tex">g\ge0</annotation></semantics></math> 表示本次已验证终点上的各对接触均达到阈值。本文不公开实际项目的阈值、插入终点或尺寸标定值。</p>
<p>每个 case 按自己的最小值排名，再比较不同 case 的最小值。最弱接触对可以随公差或姿态改变，不能先选定一对、再一直盯着它搜索。输出逗号分隔值（Comma-Separated Values，CSV）时，同时保存全部通道的曲线、终点值和最弱对身份，便于检查排名为什么变化。</p>
<p>还有一个比取最小值更重要的前提：<strong>终点必须真的到达。</strong>系统应核对最终分析步、步时间、插入位移及通道数量。一个只算到中途的低力值不能进入正常失效排名；缺失通道也不能用零填充。</p>
<h2 id="寻找应用边界而不只是最差样本">寻找应用边界，而不只是最差样本</h2>
<h3 id="先改变初始姿态再插入">先改变初始姿态，再插入</h3>
<p>若目标是“歪着插进去”，就不应先完全插入，再给一个转角。两者的接触路径不同。在固定制造公差 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi mathvariant="bold-italic">𝝃</mi><annotation encoding="application/x-tex">\boldsymbol\xi</annotation></semantics></math> 后，我使用以下坐标约定： <math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi mathvariant="bold-italic">𝒙</mi><mrow><mi mathvariant="normal">p</mi><mi mathvariant="normal">o</mi><mi mathvariant="normal">s</mi><mi mathvariant="normal">e</mi><mi mathvariant="normal">d</mi></mrow></msub><mo>=</mo><mi mathvariant="bold-italic">𝒄</mi><mo>+</mo><mi>R</mi><mo form="prefix" stretchy="false">(</mo><mi>θ</mi><mo>,</mo><mi mathvariant="bold-italic">𝒂</mi><mo form="postfix" stretchy="false">)</mo><mo form="prefix" maxsize="120%" minsize="120%" stretchy="true">(</mo><msub><mi mathvariant="bold-italic">𝒙</mi><mrow><mi mathvariant="normal">t</mi><mi mathvariant="normal">o</mi><mi mathvariant="normal">l</mi><mi mathvariant="normal">e</mi><mi mathvariant="normal">r</mi><mi mathvariant="normal">a</mi><mi mathvariant="normal">n</mi><mi mathvariant="normal">c</mi><mi mathvariant="normal">e</mi></mrow></msub><mo>−</mo><mi mathvariant="bold-italic">𝒄</mi><mo form="postfix" maxsize="120%" minsize="120%" stretchy="true">)</mo><mo>+</mo><mi>d</mi><mspace width="0.167em"></mspace><mi mathvariant="bold-italic">𝒗</mi><mo>,</mo></mrow><annotation encoding="application/x-tex">\begin{equation}
 \mathbf{x}_{\mathrm{posed}}=
 \mathbf{c}+R(\theta,\mathbf a)
 \bigl(\mathbf{x}_{\mathrm{tolerance}}-\mathbf{c}\bigr)
 +d\,\mathbf v,
\end{equation}</annotation></semantics></math> 其中 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi mathvariant="bold-italic">𝒄</mi><annotation encoding="application/x-tex">\mathbf c</annotation></semantics></math> 是旋转中心，<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi mathvariant="bold-italic">𝒂</mi><annotation encoding="application/x-tex">\mathbf a</annotation></semantics></math> 是旋转轴单位向量，<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>θ</mi><annotation encoding="application/x-tex">\theta</annotation></semantics></math> 是初始偏角，<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi mathvariant="bold-italic">𝒗</mi><annotation encoding="application/x-tex">\mathbf v</annotation></semantics></math> 是全局偏位方向单位向量，<math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>d</mi><annotation encoding="application/x-tex">d</annotation></semantics></math> 为有符号偏位。随后再执行预定插入过程。旋转和平移的顺序是模型定义的一部分，因为它们通常不可交换。</p>
<p>公端内部已有的局部制造偏移要随整体旋转变换，公端子结构也必须与 CORE 同步改变位置；母端保持不动。参考点、耦合控制点和接口节点都需要进入坐标检查，不能只移动能在屏幕上看到的实体网格。</p>
<h3 id="纯偏位并行粗扫再细分交叉区间">纯偏位：并行粗扫，再细分交叉区间</h3>
<p>零姿态基线通过后，在设定的正负偏位范围内并行粗扫。对按偏位幅值排序的相邻完成点，若 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>g</mi><annotation encoding="application/x-tex">g</annotation></semantics></math> 的符号改变，就形成一个已采样交叉区间。细化时不必一次只算二分中点，而可以把区间等分为 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mi>k</mi><annotation encoding="application/x-tex">k</annotation></semantics></math> 份，并行提交最多 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>k</mi><mo>−</mo><mn>1</mn></mrow><annotation encoding="application/x-tex">k-1</annotation></semantics></math> 个内部点；任务完成后再更新区间。</p>
<p>这并不假设“偏位越大，力一定越小”。粗扫发现通过、失效、再次通过时，需要保留多次交叉，并细化相应区间。主要报告从原点出发遇到的首次已采样失效边界，同时保留完整交叉信息。</p>
<p>终止条件是已发现交叉区间宽度达到偏位精度，或者触及范围、计算预算或未决错误。最终结果是一对已验证的通过点和失效点，不是仅靠插值给出的“精确极限”。若范围内没有发现失效，报告的是“该范围内未找到”，不能把搜索上限写成真实极限。</p>
<h3 id="偏位与偏角耦合把多条切片放进同一条队列">偏位与偏角耦合：把多条切片放进同一条队列</h3>
<p>在二维切片 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mo form="prefix" stretchy="false">(</mo><mi>d</mi><mo>,</mo><mi>θ</mi><mo form="postfix" stretchy="false">)</mo></mrow><annotation encoding="application/x-tex">(d,\theta)</annotation></semantics></math> 中，首先选取若干初始偏角，每个角度搜索正负偏位边界。多个切片共用队列，某条路径等待求解时，其他路径仍可推进。相邻偏角间距较大，或者边界位置、最弱接触对、切片状态变化明显时，再补充中间偏角。</p>
<p>图 <a href="#fig-search">5</a> 展示了这一流程。它更像<strong>批量自适应区间搜索</strong>，而不是强化学习。可以画出 <math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>−</mi><mo form="prefix" stretchy="false">|</mo><mi>g</mi><mo form="prefix" stretchy="false">|</mo></mrow><annotation encoding="application/x-tex">-|g|</annotation></semantics></math> 一类阈值接近度曲线帮助观察计算过程，但这种辅助分数不替代力学判据，也不意味着算法包含策略学习或价值函数训练。</p>
<figure data-latex-placement="H" id="fig-search">
<a href="/articles/connector-simulation/fig05_search.png" rel="noopener" target="_blank"><img alt="并行边界搜索的决策示意。样本完成后更新交叉区间，角度切片按规则加密；未知点不会被画成安全点。该图不包含实际接触力或临界偏角。" decoding="async" loading="lazy" src="/articles/connector-simulation/fig05_search.png" style="width:100%;height:auto"/></a>
<figcaption>并行边界搜索的决策示意。样本完成后更新交叉区间，角度切片按规则加密；未知点不会被画成安全点。该图不包含实际接触力或临界偏角。</figcaption>
</figure>
<p>同一偏角下，不同整体平移不改变子结构的内部刚度关系，因此可考虑复用已验证的该角度子结构库，并在使用层平移实例 <a href="#ref-abaqus-sub">[1]</a>。当前工程实现保留“每个不同偏角生成一次公端库”的路线，多个偏位点共享只读缓存。缓存必须校验来源和产物完整性；失败生成任务不能因为留下几个文件就被标记为可用。</p>
<h3 id="边界图必须说明自己没覆盖什么">边界图必须说明自己没覆盖什么</h3>
<p>一个“X 向偏位与绕 Y 偏角”的二维切片，不是所有平移、所有转角同时变化的完整姿态边界。固定某条公差向量的最差边界，也不自动等于随机总体的可靠性边界。如果需要概率结论，还要对制造变量和姿态空间的抽样设计、覆盖范围及统计不确定性另行分析。</p>
<p>有限粗网格可能漏掉比采样间距更窄的失效孤岛；相邻两个通过点之间也不能被数学证明处处通过。因此，结果图应保留通过/失效区间带、粗扫尺度、加密规则和未知区域，而不是把一条平滑线之外全部涂成“保证安全”。这不是措辞上的保守，而是算法实际能够支持的结论范围。</p>
<h2 id="我最终会怎样验收这样一套系统">我最终会怎样验收这样一套系统</h2>
<div aria-label="数据表，可横向滚动" class="table-scroll" role="region" tabindex="0"><table>
<caption>批量仿真与边界搜索的分层验收清单。</caption>
<thead>
<tr>
<th style="text-align: left;">检查层次</th>
<th style="text-align: left;">需要回答的问题</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">几何与接口</td>
<td style="text-align: left;">基准是否被污染？坐标是否按期望变化？固定区域、控制点和接口是否正确？</td>
</tr>
<tr>
<td style="text-align: left;">物理与数值</td>
<td style="text-align: left;">材料、接触、预压与插入步骤是否一致？畸变或不合理绑定是否影响结果？</td>
</tr>
<tr>
<td style="text-align: left;">执行与恢复</td>
<td style="text-align: left;">检查是否真的通过？求解是否完成？重试是否会重复启动仍存活的作业？</td>
</tr>
<tr>
<td style="text-align: left;">后处理</td>
<td style="text-align: left;">接触对身份是否一致？全局分量是否正确？最终时间与位移是否到达？</td>
</tr>
<tr>
<td style="text-align: left;">搜索与解释</td>
<td style="text-align: left;">边界是否由完成点支撑？未知点是否独立记录？是否交代预算、精度和覆盖范围？</td>
</tr>
</tbody>
</table></div>
<p>开发阶段可以用已知函数测试采点、并行乱序、区间收敛和恢复逻辑，用小型人工网格测试坐标变换与接口处理，再用真实导出网格检查移动和固定节点。<strong>这些测试证明的是软件行为，不是连接器的物理极限。</strong>实际部署后，仍需先完成基线、纯偏位和偏位加偏角的小规模完整求解，再扩大范围。</p>
<p>目前实现已经具备从样本生成到批量后处理的代码链路，以及带缓存、预算和状态恢复的并行姿态搜索入口；新增整体偏位与耦合路径的真实求解验收仍需在匹配的求解环境中进行。本文因此不提供未验证的极限角度、失效概率或速度倍数。</p>
<h2 class="unnumbered" id="结语把可解释性写进自动化">结语：把可解释性写进自动化</h2>
<p>回看整个过程，真正让仿真能够扩展的，不是某一个复杂算法，而是一连串清楚的约定：分区与保留自由度怎么选，幅值如何变成毫米，哪些输入在比较中保持不变，什么才算求解完成，以及边界曲线到底代表哪一块参数空间。</p>
<p>子结构降低了重复成本；录制 Tcl 把熟悉的 GUI 操作转成了可参数化动作；有界抽样把概率假设变成可复现的输入；统一队列与状态记录把批量运行变成可管理的计算过程；接触指标则把这些样本连接到可解释的边界问题。<strong>让每一条曲线都能回到输入、让每一次失败都有明确类型，比得到一张看起来很顺滑的结果图更重要。</strong></p>
<h2 class="unnumbered" id="复现与公开资料">复现与公开资料</h2>
<p>本文配图由独立 Python/Matplotlib 脚本生成，在 Tavotto 中检查与导出，再以矢量 PDF 插入 XeLaTeX 文稿。网站附带的源稿只包含匿名方法说明与演示采样，不读取真实工程文件。版本记录以公开网站仓库为准。</p>
<h2 id="references">参考资料</h2><ol>
<li id="ref-abaqus-sub"><p>Dassault Systèmes. <em>Using Substructures</em>. Abaqus documentation. <a class="uri" href="https://docs.software.vt.edu/abaqusv2025/English/SIMACAEANLRefMap/simaanl-c-superelements.htm">https://docs.software.vt.edu/abaqusv2025/English/SIMACAEANLRefMap/simaanl-c-superelements.htm</a>. 方法原理参考；API 与实际安装版本需分别核对。</p></li>
<li id="ref-abaqus-tie"><p>Dassault Systèmes. <em>Mesh Tie Constraints</em>. Abaqus documentation. <a class="uri" href="https://docs.software.vt.edu/abaqusv2025/English/SIMACAECSTRefMap/simacst-c-tiedconstraint.htm">https://docs.software.vt.edu/abaqusv2025/English/SIMACAECSTRefMap/simacst-c-tiedconstraint.htm</a>.</p></li>
<li id="ref-mckay"><p>McKay, M. D., Beckman, R. J., Conover, W. J. (1979). A Comparison of Three Methods for Selecting Values of Input Variables in the Analysis of Output from a Computer Code. <em>Technometrics</em>, 21(2), 239–245. <a class="uri" href="https://doi.org/10.1080/00401706.1979.10489755">https://doi.org/10.1080/00401706.1979.10489755</a>.</p></li>
<li id="ref-sobol"><p>Sobol’, I. M. (1967). On the distribution of points in a cube and the approximate evaluation of integrals. <em>USSR Computational Mathematics and Mathematical Physics</em>, 7(4), 86–112. <a class="uri" href="https://doi.org/10.1016/0041-5553(67)90144-9">https://doi.org/10.1016/0041-5553(67)90144-9</a>.</p></li>
<li id="ref-halton"><p>Halton, J. H. (1960). On the efficiency of certain quasi-random sequences of points in evaluating multi-dimensional integrals. <em>Numerische Mathematik</em>, 2, 84–90. <a class="uri" href="https://doi.org/10.1007/BF01386213">https://doi.org/10.1007/BF01386213</a>.</p></li>
<li id="ref-scipy-qmc"><p>SciPy. <em>Quasi-Monte Carlo submodule: scipy.stats.qmc</em>. <a class="uri" href="https://docs.scipy.org/doc/scipy/reference/stats.qmc.html">https://docs.scipy.org/doc/scipy/reference/stats.qmc.html</a>.</p></li>
<li id="ref-tavotto"><p>Tavotto. <em>Technology: script, editable figure, replay and export</em>. <a class="uri" href="https://www.tavotto.com/technology/">https://www.tavotto.com/technology/</a>.</p></li>
</ol>
<p class="article-downloads"><a href="/articles/connector-simulation/connector-simulation.pdf">中文 PDF</a> · <a href="/articles/connector-simulation/connector-simulation.en.pdf">English PDF</a> · <a href="/articles/connector-simulation/connector-simulation-sources-bilingual.zip">中英文 LaTeX 与配图源文件</a></p></article>
