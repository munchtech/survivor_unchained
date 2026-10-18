"""pytest, no Godot: the legal gate's shader fingerprint moves only with what can change coverage."""
import os
import shutil
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gate  # noqa: E402

REPO = gate.MAIN
OUTFITS_BRANCH = 'worktree-agent-a5ca10091b08dc429'


@pytest.fixture
def root(tmp_path):
    shutil.copytree(os.path.join(REPO, 'godot', 'shaders'), str(tmp_path / 'godot' / 'shaders'))
    shutil.copytree(os.path.join(REPO, 'tools', 'legal', 'motioncheck'), str(tmp_path / 'tools' / 'legal' / 'motioncheck'))
    return tmp_path


def fp(root, name='heroine_outfit'):
    return gate.shader_fp(str(root), name + '.gdshader', set())


def edit(root, name, old, new, ext='.gdshader'):
    p = root / 'godot' / 'shaders' / (name + ext)
    s = p.read_text(encoding='utf-8')
    assert old in s, old
    p.write_text(s.replace(old, new, 1), encoding='utf-8')


def test_outfits_colour_and_light_change_does_not_move_it(root):
    before = fp(root)
    try:
        new = subprocess.check_output(['git', '-C', REPO, 'show', OUTFITS_BRANCH + ':godot/shaders/heroine_outfit.gdshader']).decode('utf-8')
    except subprocess.CalledProcessError:
        pytest.skip('outfits branch not present')
    assert 'look_rig' in new
    (root / 'godot' / 'shaders' / 'heroine_outfit.gdshader').write_text(new, encoding='utf-8')
    assert fp(root) == before


def test_comment_and_rough_edits_do_not_move_it(root):
    before = fp(root)
    edit(root, 'heroine_outfit', 'ROUGHNESS = rough;', 'ROUGHNESS = rough * 0.5; // looser')
    assert fp(root) == before


def test_alpha_write_moves_it(root):
    before = fp(root, 'sheer')
    edit(root, 'sheer', 'pow(facing, 0.6)', 'pow(facing, 0.7)')
    assert fp(root, 'sheer') != before


def test_added_discard_moves_it(root):
    before = fp(root)
    edit(root, 'heroine_outfit', 'ALBEDO = clamp(', 'if (UV.x > 2.0) discard;\n\tALBEDO = clamp(')
    assert fp(root) != before


def test_vertex_edit_moves_it(root):
    before = fp(root)
    edit(root, 'heroine_outfit', 'painted = COLOR.b;', 'painted = COLOR.g;')
    assert fp(root) != before


def test_uniform_read_by_kept_code_moves_it(root):
    before = fp(root)
    edit(root, 'heroine_outfit', 'uniform float view_pull = 0.0;', 'uniform float view_pull = 0.5;')
    assert fp(root) != before


def test_uniform_read_by_kept_alpha_in_fragment_moves_it(root):
    before = fp(root, 'sheer')
    edit(root, 'sheer', 'face_alpha', 'face_alpha', )  # sanity: the name exists
    import re
    s = (root / 'godot' / 'shaders' / 'sheer.gdshader').read_text(encoding='utf-8')
    m = re.search(r'uniform float face_alpha[^;]*= ([0-9.]+);', s)
    assert m
    edit(root, 'sheer', m.group(0), m.group(0).replace(m.group(1), '0.123'))
    assert fp(root, 'sheer') != before


def test_unread_uniform_is_dropped(root):
    before = fp(root)
    edit(root, 'heroine_outfit', 'uniform float gold_floor = 0.08;', 'uniform float gold_floor = 0.5;')
    assert fp(root) == before


def test_unparsable_falls_back_to_whole_text(root):
    p = root / 'godot' / 'shaders' / 'heroine_outfit.gdshader'
    p.write_text(p.read_text(encoding='utf-8') + '\n}\n', encoding='utf-8')
    a = fp(root)
    edit(root, 'heroine_outfit', 'ROUGHNESS = rough;', 'ROUGHNESS = rough * 0.5;')
    assert fp(root) != a


class _Turn:
    def __init__(self, take_rc=0, take_raises=False):
        self.calls, self.take_rc, self.take_raises = [], take_rc, take_raises

    def __call__(self, root, verb, who, wait_min=600):
        self.calls.append((verb, who))
        if verb == 'take':
            if self.take_raises:
                raise KeyboardInterrupt
            return self.take_rc, 'busy'
        return 0, ''


def _run(monkeypatch, tmp_path, t, run_raises=False):
    monkeypatch.setattr(gate, 'turn', t)

    def fake_run(*a, **k):
        if run_raises:
            raise RuntimeError('godot died')
        return type('R', (), {'returncode': 0})()
    monkeypatch.setattr(gate.subprocess, 'run', fake_run)
    return gate.run_outfit(str(tmp_path), str(tmp_path), str(tmp_path / 'out'), 'warden', ['a'], ['a'], False, None)


def test_turn_given_back_after_a_failed_run(monkeypatch, tmp_path):
    t = _Turn()
    with pytest.raises(RuntimeError):
        _run(monkeypatch, tmp_path, t, run_raises=True)
    assert [v for v, _ in t.calls] == ['take', 'give'] and t.calls[0][1] == t.calls[1][1]


def test_turn_given_back_when_the_take_is_interrupted(monkeypatch, tmp_path):
    t = _Turn(take_raises=True)
    with pytest.raises(KeyboardInterrupt):
        _run(monkeypatch, tmp_path, t)
    assert [v for v, _ in t.calls] == ['take', 'give']


def test_no_give_when_the_take_was_refused(monkeypatch, tmp_path):
    t = _Turn(take_rc=1)
    assert 'blocked' in _run(monkeypatch, tmp_path, t)
    assert [v for v, _ in t.calls] == ['take']
