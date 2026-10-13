{#
用途：本文件同时指导模型生成摘要，并作为最终 Markdown 的排版模板。

写作要求：
- 默认使用简体中文；每个字段控制在 1–3 句话，直接表达，避免重复。
- 不单列实验结果，不强制凑满三条优势或不足。
- 除 idea 外，仅描述论文有依据的内容；缺失信息填写 N/A。
- idea 是模型提出的一个新研究想法，必须说明验证方式并标为未经验证。

表达与核对规则（参考 asd-ste100 的 STE-flavored 模式及 karpathy-guidelines）：
- 每句话表达一个主要意思，明确主语、动作和对象；已知执行者时优先使用主动语态。
- 使用直接、常见的表达，避免宣传性形容词、空泛修饰和重复描述。
- 同一概念使用同一术语；保留必要的学术术语，首次出现的不常见缩写需简要解释。
- 中文采用上述清晰表达原则，不套用英文词数或词典规则。英文描述每句尽量不超过 25 个词，避免分号和含糊的短语动词。
- 保留关键数字、比较基准、实验条件、适用范围、例外和不确定性；不得把“可能”“在特定条件下”改成确定或普遍成立的结论。
- 若缩短句子会损失科学含义，优先保留准确性。不得为了表达流畅而补充论文未说明的原因或机制。
- 生成前确认各字段的含义；遇到论文未交代的信息，使用 N/A，不自行猜测。
- 返回 JSON 前核对：事实字段均有论文依据，method 的步骤顺序正确，idea 明确为未经验证且包含验证方式。
- 仅在各字段内部应用这些规则；保持既定 JSON 字段与 Markdown 结构，不添加改写说明、规则表或 Kept as-is 附注。
- 这些规则用于提升表达清晰度，不代表通过 ASD-STE100 官方词典校验或认证。

规则来源：
- https://github.com/danyuchn/asd-ste100-skill
- https://github.com/multica-ai/andrej-karpathy-skills

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
