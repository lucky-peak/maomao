# API 设计规范

## RESTful API 设计原则

### URL 设计

- 使用名词复数形式：`/users`, `/orders`
- 使用嵌套表示关系：`/users/123/orders`
- 避免使用动词：`/getUsers` ❌

### HTTP 方法

| 方法 | 用途 | 示例 |
|------|------|------|
| GET | 获取资源 | `GET /users` |
| POST | 创建资源 | `POST /users` |
| PUT | 全量更新 | `PUT /users/123` |
| PATCH | 部分更新 | `PATCH /users/123` |
| DELETE | 删除资源 | `DELETE /users/123` |

### 响应格式

成功响应：

```json
{
  "code": 0,
  "data": { ... },
  "message": "success"
}
```

错误响应：

```json
{
  "code": 40001,
  "data": null,
  "message": "参数错误：用户名不能为空"
}
```

## 分页规范

使用 cursor-based 分页，避免 offset 分页在大数据量时的性能问题：

```json
{
  "data": [...],
  "pagination": {
    "cursor": "eyJpZCI6MTAwfQ==",
    "has_more": true,
    "limit": 20
  }
}
```
