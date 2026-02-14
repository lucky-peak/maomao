# 常见反模式

## 1. 上帝类 (God Class)

一个类承担太多职责，导致代码难以维护和测试。

### 问题示例

```python
class UserService:
    def create_user(self): ...
    def update_user(self): ...
    def delete_user(self): ...
    def send_email(self): ...
    def generate_report(self): ...
    def validate_payment(self): ...
```

### 解决方案

遵循单一职责原则，拆分为多个类：

```python
class UserRepository:
    def create(self): ...
    def update(self): ...
    def delete(self): ...

class EmailService:
    def send(self): ...

class ReportGenerator:
    def generate(self): ...
```

## 2. 魔法数字 (Magic Numbers)

代码中直接使用未解释的数字，降低可读性。

### 问题示例

```python
if user.age > 18:
    return "adult"
```

### 解决方案

使用命名常量：

```python
LEGAL_ADULT_AGE = 18

if user.age > LEGAL_ADULT_AGE:
    return "adult"
```

## 3. 过早优化 (Premature Optimization)

在性能瓶颈明确之前就进行优化，增加代码复杂度。

### 解决方案

- 先保证代码正确和清晰
- 使用性能分析工具定位瓶颈
- 针对性优化

## 4. 硬编码配置 (Hardcoded Configuration)

将配置信息硬编码在代码中，导致部署困难。

### 问题示例

```python
DATABASE_URL = "postgresql://user:pass@localhost:5432/mydb"
```

### 解决方案

使用环境变量或配置文件：

```python
import os
DATABASE_URL = os.environ.get("DATABASE_URL")
```
