# Jefest MCP Server

Кросс-проектный оркестратор для Claude Code. Распределяет задачи на основе SDD-спецификаций между Sonnet-агентами в нескольких проектах. Доступен как Docker-контейнер (MCP-сервер) или набор автономных PowerShell-скриптов.

[English version](README.en.md) | Лицензия Apache 2.0

## Архитектура

```
┌─────────────────────────────────────────────┐
│  Opus (планировщик)                         │
│  Пишет SDD → вызывает dispatch              │
└──────────────┬──────────────────────────────┘
               │ MCP tool call / PowerShell
┌──────────────▼──────────────────────────────┐
│  Jefest (оркестратор)                       │
│  Валидирует SDD, внедряет skills, запускает │
│  Sonnet-агента в worktree проекта           │
└──────────────┬──────────────────────────────┘
               │ claude --permission-mode bypassPermissions
┌──────────────▼──────────────────────────────┐
│  Sonnet (исполнитель)                       │
│  Читает SDD, выполняет задачи, коммитит    │
│  Пишет result-<project>.json, /exit         │
└─────────────────────────────────────────────┘
```

## Два режима работы

| | Docker (MCP-сервер) | Автономные скрипты |
|---|---|---|
| Интерфейс | MCP over HTTP | PowerShell CLI |
| Установка | `docker compose up -d` | Скопировать скрипты |
| RLM | Встроен | Опционально |
| ОС | Linux-контейнер | Windows |
| Подходит для | Продакшн, CI | Локальная разработка |

---

## Режим 1: Docker (MCP-сервер)

### Быстрый старт

```bash
cp .env.example .env
# Отредактируйте .env: укажите ANTHROPIC_API_KEY и WORKSPACE_PATH
docker compose up -d
```

### Подключение к Claude Code

```json
{
  "mcpServers": {
    "jefest": {
      "url": "http://localhost:8300/mcp"
    }
  }
}
```

### Конфигурация

| Переменная | По умолчанию | Описание |
|---|---|---|
| `ANTHROPIC_API_KEY` | обязательно | API-ключ Anthropic |
| `WORKSPACE_PATH` | `./workspace` | Путь к вашим проектам |
| `JEFEST_PORT` | `8300` | Порт MCP-сервера |
| `JEFEST_DEFAULT_MODEL` | `sonnet` | Модель Claude для диспатча |
| `RLM_EMBEDDING_PROVIDER` | `fastembed` | Бэкенд эмбеддингов RLM |

### MCP-инструменты

| Инструмент | Статус | Описание |
|---|---|---|
| `health` | stable | Здоровье сервера + статус RLM |
| `list_skills` | stable | Список доступных скиллов |
| `registry_lookup` | stable | Поиск проектов по запросу |
| `list_projects` | stable | Список всех проектов |
| `create_sdd` | stable | Генерация SDD из шаблона |
| `write_sdd` | stable | Запись SDD в workspace |
| `dispatch` | stub | Диспатч SDD агенту |
| `validate_sdd` | stub | Валидация формата SDD |
| `get_result` | stub | Получение результата диспатча |

### Свой реестр проектов

```bash
cp registry.yaml.example workspace/registry.yaml
# Добавьте свои проекты
```

### Свои скиллы

```yaml
# docker-compose.yml
volumes:
  - ./my-skills:/app/skills
```

---

## Режим 2: Автономные скрипты

Для тех, кому не нужен Docker. Чистый PowerShell, без сервера.

### Требования

- Windows, PowerShell 5.1+
- [Claude Code CLI](https://github.com/anthropics/claude-code)
- Git
- Windows Terminal (опционально)

### Установка

```powershell
# Скопируйте скрипты в удобное место
Copy-Item -Recurse standalone/ C:/tools/jefest/
```

### Написание SDD

```powershell
Copy-Item C:/tools/jefest/sdd-template.md myproject/openspec/specs/my-task-20260305.md
# Заполните: Context, Atomic Tasks, Acceptance, Finalize
```

Секция Finalize должна содержать шаг записи result-JSON и `/exit`.

### Валидация и диспатч

```powershell
# Структурная проверка
./standalone/validate-sdd.ps1 -SddPath myproject/openspec/specs/my-task.md

# Запуск агента
./standalone/dispatch-lite.ps1 -ProjectPath C:/workspace/myproject -SddPath myproject/openspec/specs/my-task.md
```

### Параметры

```
-Model haiku|sonnet|opus    Модель Claude (по умолчанию: sonnet)
-Profile budget|balanced    budget форсирует модель haiku
-Force                      пропустить валидацию, обойти блокировку
-NewProject                 разрешить несуществующий ProjectPath
```

### Мониторинг результатов

```powershell
# Результат, записанный агентом по завершении
Get-Content $env:TEMP/jefest-dispatch/result-myproject.json | ConvertFrom-Json

# Структурная проверка выполнения
./standalone/verify-completion.ps1 -SddPath ... -ProjectPath ...
```

---

## Система скиллов

Скиллы внедряют доменные знания в системный промпт агента. Укажите их в SDD:

```markdown
## Environment
- Skills: docker-expert, python-patterns, testing-patterns
```

Скиллы загружаются из:
1. `~/.claude/skills/<skill-name>/SKILL.md` (глобальные)
2. `<project>/.claude/skills/<skill-name>/SKILL.md` (проектные)

Встроенные скиллы (`skills/`):
- `docker-expert` — Docker на Proxmox/Linux
- `powershell-windows` — паттерны PowerShell
- `workflow-automation` — CI/CD и автоматизация
- `python-patterns` — Python для инфраструктуры
- `testing-patterns` — юнит- и интеграционное тестирование
- `security-audit` — аудит безопасности (OWASP)
- `api-expert` — проектирование REST/GraphQL API

Скиллы для 1С — см. [1c-ai-development-kit](https://github.com/Arman-Kudaibergenov/1c-ai-development-kit).

---

## Формат SDD

SDD (Software Design Document) — контракт между планировщиком и исполнителем.

```markdown
# SDD: <название>

## Context
## Environment
- Project: <имя>, path: <путь>
- Skills: skill1, skill2

## Atomic Tasks
1. Создать worktree: git worktree add ...
2. ...

## Acceptance
- Проверяемое условие

## Finalize
1. Коммит + пуш
2. Записать result-JSON
3. /exit
```

Полный шаблон: `standalone/sdd-template.md`.

---

## Разработка

```bash
pip install -e .
python -m jefest.server
```

---

## Лицензия

Apache 2.0. См. [LICENSE](LICENSE).
