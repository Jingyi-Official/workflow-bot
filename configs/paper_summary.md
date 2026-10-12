{#
用途：本文件同时指导模型生成摘要，并作为最终 Markdown 的排版模板。

写作要求：
- 默认使用简体中文；每个字段控制在 1–3 句话，直接表达，避免重复。
- 不单列实验结果，不强制凑满三条优势或不足。
- 除 idea 外，仅描述论文有依据的内容；缺失信息填写 N/A。
- idea 是模型提出的一个新研究想法，必须说明验证方式并标为未经验证。

编辑方式：
- 可以修改标题、顺序、语言及字段说明；保留需要展示的 {{ 字段名 }} 占位符。
- 可用字段：paper_title、paper_url、task、input、output、motivation、core_idea、method、pros、cons、idea。
- paper_title 和 paper_url 由 arXiv 检索流程提供；新增字段需同步修改 bots/openai_bot.py 的 JSON_SCHEMA。
#}
### {% if paper_url %}[{{ paper_title }}]({{ paper_url }}){% else %}{{ paper_title }}{% endif %}

#### 1. Objective
{#
字段说明：
- task：简述研究问题或目标，可包含论文明确提到的应用场景。
- input：说明方法的输入数据、数据形式及必要条件。
- output：说明方法的输出结果及其形式。
- motivation：说明现有方法的关键不足，以及本文要解决的技术挑战。
#}
- **Task**：{{ task }}
    - **Input**：{{ input }}
    - **Output**：{{ output }}
- **Motivation**：{{ motivation }}

#### 2. Summary / Key Nuggets
{#
字段说明：
- core_idea：概括主要创新，并说明它如何应对上述技术挑战。
- method：概括实现流程及关键机制；避免重复核心思路或堆砌实现细节。几句话描述这篇论文的Pipeline：第一步做了什么，第二步做了什么，第三步做了什么。
#}
- **核心思路**：{{ core_idea }}
- **方法**：{{ method }}

#### 3. Evaluation / Future Directions
{#
字段说明：
- pros：指出最值得借鉴的发现或设计，并简述其价值。
- cons：指出论文有依据的局限、适用条件或未解决的问题；不要凭空推断。
- idea：针对上述不足提出一个具体的改进方向或研究假设，并说明如何验证。
  不得冒充论文结论，也不得保证该想法在已有研究中从未出现。
#}
- **优势**：{{ pros }}
- **不足**：{{ cons }}
- **Idea（模型建议，尚未经验证）**：{{ idea }}

---
