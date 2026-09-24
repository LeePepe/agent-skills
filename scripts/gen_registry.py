#!/usr/bin/env python3
"""扫描 skills/<category>/<name>/SKILL.md 的 frontmatter,产出两样东西:
  1) registry:  skills.json(机器可读索引)
  2) 每个 skill 的 .claude-plugin/plugin.json(与 SKILL.md 同源,避免手写漂移)
并把 README 的 <!-- SKILLS:BEGIN --> ... <!-- SKILLS:END --> 区块重写成分类表。

用法:
  python3 scripts/gen_registry.py          # 生成/更新 skills.json + 各 plugin.json + README 表
  python3 scripts/gen_registry.py --check   # 只校验(CI 用):有漂移则非零退出,不改文件

纯 stdlib,不依赖第三方 YAML(frontmatter 只取 name/description/user-invocable,够用)。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
REGISTRY = ROOT / "skills.json"
README = ROOT / "README.md"
CATEGORY_ORDER = ["workflow", "design", "repo", "research", "meta"]
CATEGORY_TITLE = {"workflow": "Workflow 编排", "design": "设计", "repo": "Repo 工程", "research": "调研", "meta": "元/工具"}


def parse_frontmatter(text):
    """从 SKILL.md 取 frontmatter。返回 dict(只解析扁平标量字段)。"""
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    fm, out = m.group(1), {}
    for key in ("name", "description", "user-invocable", "allowed-tools"):
        # [ \t] 而非 \s:\s 含 \n,值为空时会跨行贪到下一字段
        km = re.search(rf"^{re.escape(key)}:[ \t]*(.*?)[ \t]*$", fm, re.M)
        if km and km.group(1).strip():
            val = km.group(1).strip()
            if len(val) >= 2 and val[0] in "'\"" and val[-1] == val[0]:
                val = val[1:-1]
            out[key] = val
    return out


def discover():
    """遍历 skills/<category>/<name>/SKILL.md,返回有序 skill 列表。"""
    skills = []
    for cat in CATEGORY_ORDER:
        cdir = SKILLS_DIR / cat
        if not cdir.is_dir():
            continue
        for sdir in sorted(p for p in cdir.iterdir() if p.is_dir()):
            sk = sdir / "SKILL.md"
            if not sk.is_file():
                continue
            fm = parse_frontmatter(sk.read_text(encoding="utf-8"))
            name = fm.get("name") or sdir.name
            skills.append({
                "name": name,
                "category": cat,
                "path": str(sdir.relative_to(ROOT)),
                "description": fm.get("description", ""),
                "user_invocable": fm.get("user-invocable", "") == "true",
                "has_references": (sdir / "references").is_dir(),
                "has_eval": (sdir / "references" / "eval-cases.md").is_file(),
            })
    return skills


def render_registry(skills):
    return json.dumps(
        {"version": "0.1.0", "count": len(skills), "skills": skills},
        ensure_ascii=False, indent=2,
    ) + "\n"


def render_plugin_json(sk):
    return json.dumps(
        {"name": sk["name"], "description": sk["description"], "category": sk["category"]},
        ensure_ascii=False, indent=2,
    ) + "\n"


def render_readme_table(skills):
    lines = []
    for cat in CATEGORY_ORDER:
        group = [s for s in skills if s["category"] == cat]
        if not group:
            continue
        lines.append(f"### {CATEGORY_TITLE[cat]}（`skills/{cat}/`）\n")
        lines.append("| Skill | 作用 |")
        lines.append("|---|---|")
        for s in group:
            desc = s["description"].replace("\n", " ").strip()
            if len(desc) > 220:
                desc = desc[:217] + "…"
            lines.append(f"| [`{s['name']}`](./{s['path']}/) | {desc} |")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def splice_readme(readme_text, table):
    begin, end = "<!-- SKILLS:BEGIN -->", "<!-- SKILLS:END -->"
    block = f"{begin}\n{table}{end}"
    if begin in readme_text and end in readme_text:
        return re.sub(re.escape(begin) + r".*?" + re.escape(end), block, readme_text, flags=re.S)
    # 无锚点则不动 README(交给人首次放锚点),返回原文
    return readme_text


def main():
    check = "--check" in sys.argv
    skills = discover()
    if not skills:
        print("no skills found under skills/<category>/", file=sys.stderr)
        return 1

    artifacts = {REGISTRY: render_registry(skills)}
    for sk in skills:
        pj = ROOT / sk["path"] / ".claude-plugin" / "plugin.json"
        artifacts[pj] = render_plugin_json(sk)
    if README.is_file():
        new_readme = splice_readme(README.read_text(encoding="utf-8"), render_readme_table(skills))
        artifacts[README] = new_readme

    drift = []
    for path, content in artifacts.items():
        old = path.read_text(encoding="utf-8") if path.is_file() else None
        if old != content:
            drift.append(path.relative_to(ROOT))
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")

    if check:
        if drift:
            print("❌ registry/plugin.json/README 与 SKILL.md 不同步,请跑 scripts/gen_registry.py:")
            for d in drift:
                print(f"   - {d}")
            return 1
        print("✅ registry / plugin.json / README 均与 SKILL.md 同步")
        return 0

    if drift:
        print("已更新:")
        for d in drift:
            print(f"   - {d}")
    else:
        print("无变化,已是最新")
    return 0


if __name__ == "__main__":
    sys.exit(main())
