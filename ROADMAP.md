# Maomao 未来发展路线图

> 本文档记录项目的未来待办事项，包含具体内容、潜在价值和相关上下文信息。
> 创建时间：2026-02-14

---

## 核心定位

**Maomao 关注的是代码背后隐藏知识的沉淀与共享**——这些知识是程序员认为值得精心提炼、无法通过代码自动学习到的精华内容。我们支持的知识类型类似于 "code space" 概念所涵盖的范畴，是特定于某个代码库或项目的背景知识与经验总结。

```
┌─────────────────────────────────────────────────────────────────┐
│                        知识类型对比                              │
├─────────────────────────────────────────────────────────────────┤
│  AI 可自动学习                    │  需要人工沉淀（本项目目标）    │
├───────────────────────────────────┼─────────────────────────────┤
│  函数签名、类结构                  │  为什么选择这个设计方案        │
│  代码调用关系                      │  业务规则的背景和演变历史      │
│  变量命名模式                      │  曾经踩过的坑和教训           │
│  代码重复检测                      │  某个奇怪代码存在的原因        │
│  测试覆盖率                        │  与其他系统的隐式约定         │
│  ...                              │  团队积累的领域知识           │
└───────────────────────────────────┴─────────────────────────────┘
```

---

## 高优先级

### 1. 交互式知识采集

**具体内容**：
- 提供 `maomao interview` 命令，启动 AI 驱动的知识访谈模式
- AI 分析代码中的"可疑点"（复杂逻辑、大量注释、特殊处理）
- 生成针对性问题，引导用户补充背景知识
- 自动整理成结构化知识条目存入知识库

**潜在价值**：
- 降低知识沉淀门槛，解决"知识在老员工脑子里"的问题
- 变被动记录为主动采集，提高知识库的完整性
- 特别适合 legacy 系统的知识抢救场景

**相关上下文**：
- Legacy 系统最大的挑战是知识分散在有经验的员工脑子里
- 需要低摩擦地提取这些隐性知识
- AI 可以根据代码特征智能提问，引导用户回忆和记录

**实现要点**：
```bash
# 示例命令
maomao interview --project legacy-payment

# AI 根据代码特征提问：
# "我看到 PaymentService.calculateDiscount() 有很多边界条件处理，
#  这些规则是从哪些业务需求演变来的？有哪些坑？"
#
# 用户回答后自动整理成知识条目
```

---

### 2. 代码关联式知识记录

**具体内容**：
- 提供 `maomao note add` 命令，支持在代码旁边记录知识
- 知识与代码位置（文件、行号范围）关联
- 当代码变更时，提醒验证知识是否需要更新
- AI 编辑代码时，自动检索相关知识并展示

**潜在价值**：
- 让知识与代码位置绑定，形成"活文档"
- AI 编辑代码时自动获取相关背景知识
- 解决"文档和代码分离"的经典问题

**相关上下文**：
- 传统文档与代码分离，容易过时且难以发现
- 知识需要与具体代码位置关联才有意义
- AI 编辑代码时需要知道"为什么这样写"

**实现要点**：
```bash
# 在代码旁边记录知识
maomao note add --file src/payment.py --line 150-200

# 打开编辑器，记录：
# """
# ## 折扣计算逻辑说明
# 
# 这段代码看起来复杂，是因为需要处理三种历史遗留的折扣规则：
# 1. 2019年前的会员折扣（已废弃但需要兼容）
# 2. 2020年促销活动折扣（临时方案变成了永久）
# 3. 当前的新折扣体系
# 
# 注意：不要删除任何分支，老数据依赖它们
# """
```

**数据模型扩展**：
```python
class KnowledgeChunk(BaseModel):
    # ... 现有字段
    related_code_paths: list[str] = []  # 关联的代码路径
    code_location: CodeLocation | None = None  # 具体代码位置
```

---

### 3. 变更触发验证提醒

**具体内容**：
- 提供 Git hook 或 CI 集成，监控代码变更
- 当关联代码变更时，提醒验证知识是否需要更新
- 提供 `maomao watch` 命令配置监控

**潜在价值**：
- 保证知识时效性，防止过时知识误导 AI
- 形成知识维护的闭环机制
- 降低知识维护的心智负担

**相关上下文**：
- Legacy 系统的知识容易过时
- 代码变更后，相关知识可能不再准确
- 需要机制提醒用户验证和更新

**实现要点**：
```bash
# Git hook 集成
maomao watch --hook post-commit

# 当关联代码变更时：
# ⚠️  知识 "折扣计算逻辑说明" 关联的代码已变更
#    文件: src/payment.py (lines 150-200)
#    请验证知识是否需要更新
```

---

## 中优先级

### 4. 知识继承与覆盖

**具体内容**：
- 支持项目间知识继承配置
- 提供 `extend`（扩展）和 `override`（覆盖）两种模式
- 支持按知识类别选择性继承
- 提供知识冲突检测功能

**潜在价值**：
- 跨项目共享知识，实现 "code space" 的复用价值
- 新项目可以快速继承平台/基座项目的知识
- 避免重复记录相同的知识

**相关上下文**：
- 多个项目可能共享同一平台核心
- 相似的业务场景有相似的知识需求
- "code space" 概念强调知识的可复用性

**实现要点**：
```json
{
  "sources": [
    {
      "type": "knowledge_inheritance",
      "from_project": "platform-core",
      "knowledge_scope": "project",
      "config": {
        "inherit_mode": "extend",
        "categories": ["error-handling", "logging", "security"]
      }
    }
  ]
}
```

**冲突检测**：
```bash
maomao sync --from project-a --to project-b

# ⚠️  检测到知识冲突：
# 
# 项目 A: "错误码 500 表示系统异常，需要告警"
# 项目 B: "错误码 500 是正常重试，不需要告警"
# 
# 请确认项目 B 的知识是否正确
```

---

### 5. 上下文感知知识推荐

**具体内容**：
- 新增 MCP 工具 `get_relevant_knowledge`
- 根据当前编辑上下文（文件、选中代码、任务描述）自动推荐相关知识
- AI 无需显式搜索，自动获取背景知识

**潜在价值**：
- 让 AI 主动获取相关知识，而非被动等待搜索
- 提高知识的实际使用率
- 减少用户手动查询的负担

**相关上下文**：
- 当前 MCP 工具需要 AI 主动调用搜索
- AI 可能不知道何时应该搜索知识
- 根据上下文主动推送更智能

**实现要点**：
```typescript
// 新增 MCP 工具
{
  name: "get_relevant_knowledge",
  description: "根据当前编辑上下文获取相关知识",
  parameters: {
    current_file: string,      // 当前文件路径
    selected_code: string,     // 选中的代码片段
    task_description: string   // 正在执行的任务描述
  }
}

// AI 调用示例：
// 正在修改 payment.py 的折扣逻辑
// → 自动返回相关知识："折扣计算逻辑说明"、"折扣历史演变"
```

---

### 6. 知识健康度报告

**具体内容**：
- 提供 `maomao health` 命令，生成知识库健康度报告
- 评估维度：验证状态、时效性、覆盖率
- 提供优先验证建议

**潜在价值**：
- 可视化知识库质量
- 帮助团队识别需要关注的知识区域
- 形成知识维护的常规流程

**相关上下文**：
- 知识库需要持续维护
- 需要工具帮助识别问题区域
- 团队需要了解知识库的整体状态

**实现要点**：
```bash
maomao health --project legacy-payment

# 输出：
# 知识库健康度报告
# ==================
# 总知识条目: 45
# ✅ 已验证: 28 (62%)
# ⚠️  需要验证: 12 (27%) - 关联代码已变更
# ❓ 未验证: 5 (11%) - 新增未验证
# 
# 建议优先验证：
# 1. "支付回调处理" - 关联代码 30 天前变更
# 2. "订单状态机" - 关联代码 7 天前变更
```

---

## 低优先级

### 7. 知识缺口检测

**具体内容**：
- 新增 MCP 工具 `detect_knowledge_gap`
- 分析代码复杂度与知识覆盖的关系
- 建议需要补充知识的代码区域

**潜在价值**：
- 发现需要补充知识的地方
- 主动提示用户记录重要知识
- 提高知识库的覆盖率

**相关上下文**：
- 复杂代码区域更需要背景知识
- 用户可能不知道哪些地方需要记录
- AI 可以帮助识别知识盲区

**实现要点**：
```typescript
{
  name: "detect_knowledge_gap",
  description: "检测代码区域是否有足够的知识覆盖",
  parameters: {
    file: string,
    complexity_threshold: number  // 复杂度阈值
  }
}

// 返回：
// "检测到 src/payment.py:150-200 复杂度较高但无知识覆盖
//  建议补充：这段代码的业务背景或注意事项"
```

---

### 8. 知识质量评分

**具体内容**：
- 建立知识质量评估体系
- 评估维度：完整性、时效性、引用率、用户反馈
- 支持知识去重与合并

**潜在价值**：
- 持续提升知识库质量
- 激励用户贡献高质量知识
- 自动识别低质量或重复知识

**相关上下文**：
- 知识质量参差不齐
- 需要机制激励高质量贡献
- 重复知识会造成混淆

**实现要点**：
```python
class KnowledgeQuality:
    """知识质量评估"""
    
    def evaluate(self, chunk: KnowledgeChunk) -> QualityScore:
        # 评估维度：
        # - 完整性：是否包含背景、原因、注意事项
        # - 时效性：上次验证时间
        # - 引用率：被 AI 引用的次数
        # - 反馈：用户标记的有用/无用
        pass
```

**去重功能**：
```bash
maomao dedup --project legacy-payment

# 检测到相似知识：
# 1. "支付回调处理" (siyuan://blocks/abc)
# 2. "支付回调注意事项" (local_doc/docs/payment.md)
# 
# 建议合并？[Y/n]
```

---

### 9. 知识模板化

**具体内容**：
- 支持将项目知识抽象成模板
- 模板可应用到新项目
- AI 辅助确认模板知识的适用性

**潜在价值**：
- 加速新项目的知识库建设
- 沉淀行业/领域最佳实践
- 降低知识整理的重复劳动

**相关上下文**：
- 相似项目有相似的知识需求
- 某些知识具有通用性
- 模板化可以提高效率

**实现要点**：
```bash
# 将某项目的知识抽象成模板
maomao template extract --project project-a --output payment-knowledge-template.json

# 应用到新项目
maomao template apply --template payment-knowledge-template.json --project project-b

# AI 会提示：
# "检测到项目 B 也有支付模块，以下是项目 A 的支付相关知识，
#  请确认哪些适用于本项目，哪些需要调整"
```

---

### 10. 从对话中提取知识

**具体内容**：
- 分析 AI 与用户的对话记录
- 自动识别值得沉淀的知识片段
- 生成知识草稿供用户确认

**潜在价值**：
- 捕捉对话中产生的有价值知识
- 减少人工整理的工作量
- 形成知识沉淀的自然流程

**相关上下文**：
- 开发过程中会产生大量有价值的讨论
- 这些知识往往散落在对话中
- 自动提取可以提高知识捕获率

**实现要点**：
```python
class ConversationKnowledgeExtractor:
    """从 AI 对话中提取知识"""
    
    def extract_from_conversation(self, conversation: list[Message]) -> list[KnowledgeDraft]:
        # 识别模式：
        # - 用户解释了业务背景
        # - 用户纠正了 AI 的理解
        # - 用户提到了历史原因
        # - 用户分享了踩坑经验
        pass
```

---

## 数据模型扩展汇总

为支持上述功能，需要对现有数据模型进行扩展：

```python
class KnowledgeChunk(BaseModel):
    id: str
    content: str
    source_type: str
    source_path: str
    source_id: str
    knowledge_scope: str = "global"
    project_id: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    content_hash: str = ""
    embedding: list[float] | None = None
    location: ChunkLocation | None = None
    
    # === 新增字段 ===
    # 知识验证相关
    confidence: Literal["verified", "likely", "uncertain"] = "likely"
    verified_by: str = ""
    verified_at: datetime | None = None
    
    # 代码关联相关
    related_code_paths: list[str] = []
    code_location: CodeLocation | None = None
    
    # 知识质量相关
    reference_count: int = 0  # 被 AI 引用的次数
    helpful_count: int = 0    # 用户标记"有用"的次数
    not_helpful_count: int = 0  # 用户标记"无用"的次数


class CodeLocation(BaseModel):
    """代码位置信息"""
    file_path: str
    line_start: int
    line_end: int
    symbol_name: str | None = None  # 关联的符号名（函数/类名）
```

---

## MCP 工具扩展汇总

| 工具名 | 说明 | 优先级 |
|--------|------|--------|
| `get_relevant_knowledge` | 根据上下文获取相关知识 | 中 |
| `detect_knowledge_gap` | 检测知识覆盖缺口 | 低 |
| `suggest_knowledge_reference` | 建议在代码中引用知识 | 低 |

---

## CLI 命令扩展汇总

| 命令 | 说明 | 优先级 |
|------|------|--------|
| `maomao interview` | 交互式知识采集 | 高 |
| `maomao note add` | 添加代码关联知识 | 高 |
| `maomao watch` | 配置变更监控 | 高 |
| `maomao health` | 知识库健康度报告 | 中 |
| `maomao sync` | 跨项目知识同步 | 中 |
| `maomao dedup` | 知识去重 | 低 |
| `maomao template extract/apply` | 知识模板管理 | 低 |

---

## 实施原则

1. **渐进式开发**：按优先级逐步实现，每个功能独立可用
2. **用户反馈驱动**：根据实际使用反馈调整优先级和实现方式
3. **保持核心定位**：始终聚焦于"人工提炼的隐性知识"，不与 AI 自动学习能力竞争
4. **低摩擦设计**：所有功能都应降低知识沉淀和管理的门槛
