# PrefHub

AI 项目生态的统一用户偏好管理库。

## 解决什么问题

多个 AI 项目（ai-audio-assistant、idea-generator、prompthub）都需要管理用户偏好（语言、主题、通知、时区等），但每个项目各写一套，导致：

- 重复的 merge/CRUD 逻辑
- 偏好字段不一致（一个叫 `locale`，另一个叫 `language`）
- 新项目需要从头写偏好系统

PrefHub 把**通用偏好**抽成共享库，各项目只需扩展**业务特有偏好**。

## 架构

```
prefhub (共享库)
├── schemas/          # 通用 Pydantic schemas
│   ├── __init__.py   # Theme, Language, HourCycle 枚举
│   └── preferences.py # UIPreferences, NotificationPreferences, BasePreferences
├── services/         # 存储无关的 CRUD + merge 逻辑
│   └── preferences.py # PreferencesService (abstract), deep_merge
├── models/           # SQLAlchemy mixins（可选）
│   └── mixins.py     # PreferencesEmbeddedMixin, PreferencesTableMixin
└── api/              # FastAPI router 工厂（可选）
    └── __init__.py   # create_preferences_router()
```

## 快速开始

### 安装

```bash
# 基础（只要 schemas + service）
pip install git+https://github.com/HyxiaoGe/prefhub.git

# 含 SQLAlchemy 支持
pip install "prefhub[sqlalchemy] @ git+https://github.com/HyxiaoGe/prefhub.git"

# 含 FastAPI 路由支持
pip install "prefhub[fastapi] @ git+https://github.com/HyxiaoGe/prefhub.git"

# 全部
pip install "prefhub[all] @ git+https://github.com/HyxiaoGe/prefhub.git"
```

### 1. 扩展你的项目偏好

```python
from pydantic import BaseModel, Field
from prefhub.schemas.preferences import BasePreferences

class AudioTaskDefaults(BaseModel):
    summary_style: str = "meeting"
    asr_provider: str | None = None

class MyPreferences(BasePreferences):
    """继承通用偏好，添加业务字段"""
    task_defaults: AudioTaskDefaults = Field(default_factory=AudioTaskDefaults)
```

### 2. 实现存储后端

```python
from prefhub.services.preferences import PreferencesService

class MyPreferencesService(PreferencesService):
    async def _load_raw(self, user_id: str) -> dict:
        row = await db.get_user_settings(user_id)
        return row.preferences if row else {}

    async def _save_raw(self, user_id: str, data: dict) -> None:
        await db.upsert_settings(user_id, preferences=data)
```

### 3. 挂载 API

```python
from prefhub.api import create_preferences_router

router = create_preferences_router(
    get_service=lambda: MyPreferencesService(db),
    get_user_id=get_current_user_id,
    prefix="/api/v1/preferences",
)
app.include_router(router)
```

自动生成三个端点：
- `GET /api/v1/preferences` — 获取偏好（含默认值）
- `PATCH /api/v1/preferences` — 增量更新
- `DELETE /api/v1/preferences` — 重置为默认

## 支持的存储模式

| 模式 | 适用项目 | Mixin |
|------|---------|-------|
| Pattern A: 嵌入 User.settings JSONB | ai-audio-assistant | `PreferencesEmbeddedMixin` |
| Pattern B: 独立 user_settings 表 | idea-generator | `PreferencesTableMixin` |

两种模式的 service 层接口完全相同，只是 `_load_raw` / `_save_raw` 实现不同。

## 通用偏好字段

| 分类 | 字段 | 类型 | 默认值 |
|------|------|------|--------|
| UI | language | Language | zh-CN |
| UI | theme | Theme | system |
| UI | timezone | str | Asia/Shanghai |
| UI | hour_cycle | HourCycle | auto |
| 通知 | enabled | bool | true |
| 通知 | task_completed | bool | true |
| 通知 | task_failed | bool | true |
| 通知 | sound | bool | false |

## 开发

```bash
git clone https://github.com/HyxiaoGe/prefhub.git
cd prefhub
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT
