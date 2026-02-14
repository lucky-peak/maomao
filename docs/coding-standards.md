# Maomao 编码规范

## 项目命名规范

### 文件命名

- Python 文件使用小写下划线命名：`my_module.py`
- TypeScript 文件使用小写连字符命名：`my-component.tsx`
- 测试文件以 `_test.py` 或 `.test.ts` 结尾

### 变量命名

- 变量使用 snake_case：`user_name`
- 常量使用 UPPER_SNAKE_CASE：`MAX_RETRY_COUNT`
- 类名使用 PascalCase：`UserService`

## 代码风格

### Python

使用 ruff 进行代码检查，主要规则：

- 行长度限制：100 字符
- 使用 f-string 格式化字符串
- 类型注解必须完整

### TypeScript

使用 ESLint + Prettier，主要规则：

- 使用单引号
- 末尾不加分号
- 使用 2 空格缩进

## 最佳实践

### 错误处理

不要使用裸 except，应该捕获具体异常：

```python
# 好的做法
try:
    result = do_something()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
except ConnectionError as e:
    logger.error(f"Connection failed: {e}")

# 不好的做法
try:
    result = do_something()
except:
    pass  # 吞掉所有异常
```

### 日志规范

- 使用结构化日志
- 包含上下文信息
- 合理设置日志级别
