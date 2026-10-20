# Work1 Secure REST API

基于 FastAPI 的安全 REST API 实验项目：实现 JWT 认证、bcrypt 密码哈希与参数化查询防 SQL 注入。

## 1. 项目简介

本项目是一个带完整认证与安全防护的 REST API，包含登录、数据获取与个人资料三个接口。所有受保护接口均要求携带有效的 JWT Bearer Token 才能访问。

## 2. 技术栈

- Python 3.12
- FastAPI + Uvicorn
- PyJWT（JWT 签发与校验，HS256）
- bcrypt（密码哈希）
- SQLite（数据存储，参数化查询）

## 3. 环境与安装

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
py -m uvicorn app:app --reload
```

服务默认监听 `http://127.0.0.1:8000`，接口文档见 `/docs`（Swagger UI）。

## 4. 接口文档

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/auth/login` | 用户名密码登录，签发 JWT | 无 |
| GET | `/api/data` | 返回受保护数据 | Bearer Token |
| GET | `/api/profile` | 返回当前用户资料 | Bearer Token |

## 5. 安全特性

- **bcrypt 密码哈希**：数据库不存明文密码。
- **参数化查询**：所有 SQL 均使用参数绑定，防止 SQL 注入。
- **JWT 认证**：登录后签发 HS256 签名 Token，过期时间 24 小时。
- **统一 401 处理**：区分"缺少令牌 / 令牌已过期 / 无效令牌"三类错误。

## 6. 测试与验证

```bash
# 登录获取 Token
curl.exe -X POST http://127.0.0.1:8000/auth/login -H "Content-Type: application/json" -d '{"username":"Qs1r","password":"Zjx123456"}'

# 携带 Token 访问受保护接口
curl.exe -H "Authorization: Bearer <token>" http://127.0.0.1:8000/api/data
curl.exe -H "Authorization: Bearer <token>" http://127.0.0.1:8000/api/profile
```

测试截图见 `docs/` 目录（curl 与 Swagger 验证结果）。

## 7. CI/CD 流水线

GitHub Actions 自动化安全扫描：

- **bandit**：Python 代码静态安全分析（SAST）。
- **Dependency-Check**：依赖库漏洞扫描（SCA）。

流水线配置见 `.github/workflows/ci.yml`，最近一次运行结果：

> 待推送后补充流水线链接

## 8. CVE 复现与修复

- **CVE-2014-6271（Shellshock）**：使用 vulhub 复现漏洞环境，分析原理并给出修复方案。
- 复现过程、截图与修复说明见 `fix/` 目录（后续补充）。
