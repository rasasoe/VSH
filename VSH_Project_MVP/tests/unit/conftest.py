"""Isolate unit-test knowledge and logs from the developer's runtime data."""
from pathlib import Path
import pytest


@pytest.fixture(autouse=True)
def isolated_repositories(tmp_path, monkeypatch, request):
    import repository.knowledge_repo as knowledge
    import repository.fix_repo as fixes
    import repository.log_repo as logs
    seed = Path(__file__).resolve().parents[2] / 'mock_db'
    knowledge_path = tmp_path / 'knowledge.json'
    fix_path = tmp_path / 'kisa_fix.json'
    log_path = tmp_path / 'log.json'
    knowledge_path.write_bytes((seed / 'knowledge.json').read_bytes())
    fix_path.write_bytes((seed / 'kisa_fix.json').read_bytes())
    log_path.write_text('[]', encoding='utf-8')
    monkeypatch.setattr(knowledge, 'KNOWLEDGE_PATH_OBJ', knowledge_path)
    monkeypatch.setattr(fixes, 'FIX_PATH_OBJ', fix_path)
    monkeypatch.setattr(logs, 'LOG_PATH', str(log_path))
    if hasattr(request.module, 'LOG_PATH'):
        monkeypatch.setattr(request.module, 'LOG_PATH', str(log_path))
