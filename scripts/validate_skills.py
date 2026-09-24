#!/usr/bin/env python3
"""校验每个 skills/<category>/<name>/SKILL.md 的 frontmatter 与引用完整性。
CI 与本地共用。有任一问题则非零退出。

校验项(对齐 Anthropic 官方 skill 规范):
  1) frontmatter 存在,含 name + description
  2) name:仅小写字母/数字/连字符,≤64 字符,不含保留词 claude/anthropic
  3) name == 目录名(避免索引错位)
  4) description:非空,≤1024 字符
  5) references 链接不断:SKILL.md 里 (path.md) 形式的本地相对链接目标必须存在
  6) 引用只下钻一层:SKILL.md 指向的 references/*.md 不应再指向另一个 references/*.md
     (官方"keep references one level deep";这里只对本 skill 内的 references 告警,不 fail)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
RESERVED = ("claude", "anthropic")
NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")
LINK_RE = re.compile(r"\]\(([^)]+\.md)\)")


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return m.group(1) if m else None


def scalar(fm, key):
    # [ \t] 而非 \s:\s 含 \n,值为空时会跨行贪到下一字段(已被负向测试抓到)
    m = re.search(rf"^{re.escape(key)}:[ \t]*(.*?)[ \t]*$", fm, re.M)
    if not m:
        return None
    v = m.group(1).strip()
    if len(v) >= 2 and v[0] in "'\"" and v[-1] == v[0]:
        v = v[1:-1]
    return v


def local_md_links(text):
    out = []
    for m in LINK_RE.finditer(text):
        target = m.group(1)
        if target.startswith(("http://", "https://", "#")):
            continue
        out.append(target)
    return out


def main():
    errors, warnings = [], []
    skills = sorted(SKILLS_DIR.glob("*/*/SKILL.md"))
    if not skills:
        print("no SKILL.md under skills/<category>/", file=sys.stderr)
        return 1

    for sk in skills:
        rel = sk.relative_to(ROOT)
        d = sk.parent
        text = sk.read_text(encoding="utf-8")
        fm = frontmatter(text)
        if fm is None:
            errors.append(f"{rel}: 缺 frontmatter")
            continue

        name = scalar(fm, "name")
        desc = scalar(fm, "description")

        if not name:
            errors.append(f"{rel}: frontmatter 缺 name")
        else:
            if not NAME_RE.match(name):
                errors.append(f"{rel}: name '{name}' 不合规(仅小写/数字/连字符,≤64)")
            if any(w in name.lower() for w in RESERVED):
                errors.append(f"{rel}: name '{name}' 含保留词(claude/anthropic)")
            if name != d.name:
                errors.append(f"{rel}: name '{name}' ≠ 目录名 '{d.name}'")

        if not desc:
            errors.append(f"{rel}: frontmatter 缺 description")
        elif len(desc) > 1024:
            errors.append(f"{rel}: description {len(desc)} 字符 > 1024 上限")

        # references 链接不断 + 一层深度
        for target in local_md_links(text):
            tp = (d / target).resolve()
            if not tp.is_file():
                errors.append(f"{rel}: 断链 -> {target}")
                continue
            # 一层深度告警:被 SKILL.md 指向的 references/*.md 又指向本 skill 内 references/*.md
            try:
                inside = d in tp.parents
            except Exception:
                inside = False
            if inside and tp.name != "SKILL.md":
                sub = tp.read_text(encoding="utf-8")
                for t2 in local_md_links(sub):
                    p2 = (tp.parent / t2).resolve()
                    if p2.is_file() and (d / "references") in p2.parents:
                        warnings.append(
                            f"{rel}: 深层引用({target} → {t2});官方建议 references 只下钻一层")
                        break

    for w in warnings:
        print(f"⚠️  {w}")
    if errors:
        print(f"\n❌ {len(errors)} 处校验失败:")
        for e in errors:
            print(f"   - {e}")
        return 1
    print(f"✅ {len(skills)} 个 SKILL.md frontmatter/链接校验通过"
          + (f"({len(warnings)} 条告警)" if warnings else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
