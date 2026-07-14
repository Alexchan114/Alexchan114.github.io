---
title: "TransGNN：Transformer 与 GNN 如何在推荐图上协作"
slug: "transgnn"
date: 2026-07-14
description: "梳理交替层结构、相关节点采样、位置编码与消息传递之间的数据流。"
tags: ["Reproduction", "Recommendation", "Graph Transformer"]
---

复现一篇模型论文时，最先需要回答的通常不是“参数设多少”，而是：**每一层到底接收什么、改变什么，又把什么交给下一层**。

TransGNN 把 Transformer 的全局交互能力和 GNN 的局部结构偏置放在同一条计算路径里。理解它的关键，是把整套流程拆成可检查的数据流，而不是把两类模块只看作名称上的组合。

## 我正在确认的问题

1. 相关节点采样在训练与推理阶段是否保持一致。
2. 位置编码携带的是距离、序列顺序，还是采样过程本身的信息。
3. Transformer 层与图消息传递层交替后，节点表示分别吸收了哪些上下文。
4. 评价提升来自架构组合，还是来自采样、负样本与训练配置。

## 复现顺序

我会先建立一个能够跑通的小规模基线，再逐项加入采样、位置编码和交替层。每一步都保留独立配置与日志，以免最终结果无法归因。

```text
baseline → sampling → position encoding → alternating blocks → full evaluation
```

> 当前状态：结构与数据流已经整理，实验结论仍需在统一的数据划分和评价协议下验证。
