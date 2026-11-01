"""全面数据验证 - 检查所有人物数据库的完整性、准确性、重复性"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FILES = {
    "real_people.json": "实时人物库",
    "master_10k.json": "万人大师库",
    "persons_merged.json": "合并人物库",
    "validation_enhanced.json": "验证集(13人)",
    "twins_collected.json": "双胞胎库",
    "seed_data.json": "种子数据",
    "real_test.json": "测试样本",
    "training_log.json": "训练日志",
    "life_timelines.json": "生命周期库",
    "pattern_db.json": "模式库",
}

def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"_error": str(e)}

def validate_person(p, source="", idx=0):
    """Validate a single person record. Returns list of issues."""
    issues = []
    name = p.get("name", p.get("Name", ""))
    if not name:
        issues.append(f"[{source}#{idx}] 缺少name字段")
        return issues

    # Check birth year
    by = p.get("birth_year", p.get("BirthYear", p.get("year", 0)))
    if not by or by < -5000 or by > 2026:
        issues.append(f"[{source}#{idx}] {name}: birth_year异常({by})")

    # Check birth month
    bm = p.get("birth_month", p.get("BirthMonth", p.get("month", 0)))
    if bm and (bm < 1 or bm > 12):
        issues.append(f"[{source}#{idx}] {name}: birth_month异常({bm})")

    # Check birth day
    bd = p.get("birth_day", p.get("BirthDay", p.get("day", 0)))
    if bd and (bd < 1 or bd > 31):
        issues.append(f"[{source}#{idx}] {name}: birth_day异常({bd})")

    # Check death year > birth year
    dy = p.get("death_year", 0)
    if dy and by and dy < by:
        issues.append(f"[{source}#{idx}] {name}: death_year({dy}) < birth_year({by})")

    # Check lifespan = death_year - birth_year
    if dy and by and (dy - by) > 120:
        issues.append(f"[{source}#{idx}] {name}: 寿命异常({dy-by}岁)")

    # Check confidence range
    conf = p.get("confidence", 1.0)
    if not (0 <= conf <= 1):
        issues.append(f"[{source}#{idx}] {name}: confidence异常({conf})")

    return issues

def check_file(filepath, label):
    """Validate a whole data file."""
    data = load_json(filepath)
    if isinstance(data, dict) and "_error" in data:
        return {"file": label, "type": "ERROR", "error": data["_error"]}

    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        # Could be name-keyed dict or figure/mentors structure
        if "figures" in data:
            items = data["figures"]
        elif "mentors" in data:
            items = data["mentors"]
        else:
            items = list(data.values())
    else:
        return {"file": label, "type": f"UNEXPECTED({type(data).__name__})", "count": "?"}

    total = len(data) if isinstance(data, list) else len(data)
    all_issues = []
    name_counts = {}
    empty_names = 0

    for idx, item in enumerate(items if isinstance(items, list) else []):
        if not isinstance(item, dict):
            continue
        name = item.get("name", item.get("Name", ""))
        if name:
            nk = name.lower().strip()
            name_counts[nk] = name_counts.get(nk, 0) + 1
        else:
            empty_names += 1
        all_issues.extend(validate_person(item, label, idx))

    # Duplicate names
    dups = {k: v for k, v in name_counts.items() if v > 1}
    
    # Summary stats
    bz_count = sum(1 for item in (items if isinstance(items, list) else []) 
                   if isinstance(item, dict) and (item.get("bazi") or item.get("Bazi")))
    death_count = sum(1 for item in (items if isinstance(items, list) else [])
                      if isinstance(item, dict) and (item.get("death_year") or item.get("death_cause")))
    occ_count = sum(1 for item in (items if isinstance(items, list) else [])
                    if isinstance(item, dict) and (item.get("occupation") or item.get("career")))

    return {
        "file": label,
        "path": filepath,
        "type": f"list[{len(items)}]" if isinstance(items, list) else f"dict[{total}]",
        "total": len(items) if isinstance(items, list) else total,
        "valid_count": len(items) if isinstance(items, list) else 0,
        "issues": all_issues,
        "issue_count": len(all_issues),
        "empty_names": empty_names,
        "duplicates": dups,
        "duplicate_count": len(dups),
        "has_bazi": bz_count,
        "has_death": death_count,
        "has_occupation": occ_count,
    }

def sample_items(filepath, n=5):
    """Sample items to show actual content quality."""
    try:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
    except:
        return []
    if isinstance(data, list):
        items = data[:n]
    elif isinstance(data, dict):
        items = list(data.values())[:n]
    else:
        return []
    samples = []
    for it in items:
        if isinstance(it, dict):
            s = {k: it.get(k) for k in ["name", "birth_year", "birth_month", "birth_day", 
                                          "death_year", "occupation", "bazi", "confidence"]
                 if k in it}
            samples.append(s)
    return samples

if __name__ == "__main__":
    data_dir = r"C:\Users\ctooc\Desktop\workspace\_ai\gcalc\data"
    
    print("="*70)
    print("  Gcalc 数据库全面验证报告")
    print("="*70)
    
    all_stats = {}
    total_issues = 0
    
    for fname, label in FILES.items():
        fpath = os.path.join(data_dir, fname)
        if not os.path.exists(fpath):
            print(f"\n[{label}] 文件不存在")
            continue
        stats = check_file(fpath, label)
        all_stats[fname] = stats
        total_issues += stats["issue_count"]
        
        print(f"\n{'='*50}")
        print(f"  [{label}] {fname}")
        print(f"{'='*50}")
        print(f"  类型: {stats['type']}")
        print(f"  记录数: {stats['total']}")
        print(f"  有八字: {stats['has_bazi']}")
        print(f"  有死亡记录: {stats['has_death']}")
        print(f"  有职业: {stats['has_occupation']}")
        print(f"  问题数: {stats['issue_count']}")
        if stats["empty_names"]:
            print(f"  空名字: {stats['empty_names']}")
        if stats["duplicate_count"]:
            print(f"  重复名字: {stats['duplicate_count']}组")
            for name, count in list(stats["duplicates"].items())[:5]:
                print(f"    {name}: {count}次")
                if len(stats["duplicates"]) > 5:
                    print(f"    ... 还有{len(stats['duplicates'])-5}组")
        if stats["issues"]:
            print(f"  前10个问题:")
            for iss in stats["issues"][:10]:
                print(f"    {iss}")
        
        # Sample
        samples = sample_items(fpath)
        if samples:
            print(f"  样本:")
            for s in samples[:3]:
                print(f"    {s}")
    
    # Overall summary
    print(f"\n\n{'='*70}")
    print("  汇总")
    print(f"{'='*70}")
    print(f"  总问题数: {total_issues}")
    
    # Cross-file consistency check: do the 13 validation figures exist elsewhere?
    print(f"\n  --- 交叉验证: master_10k vs real_people ---")
    mp = all_stats.get("master_10k.json", {})
    rp = all_stats.get("real_people.json", {})
    if mp.get("total") and rp.get("total"):
        print(f"  master_10k有{mp['total']}人, real_people有{rp['total']}人")
        # Check overlap
        try:
            with open(os.path.join(data_dir, "master_10k.json"), encoding="utf-8") as f:
                master = json.load(f)
            with open(os.path.join(data_dir, "real_people.json"), encoding="utf-8") as f:
                real = json.load(f)
            master_names = set()
            if isinstance(master, dict):
                for v in master.values():
                    if isinstance(v, dict):
                        n = v.get("name", "")
                        if n:
                            master_names.add(n.lower().strip())
            elif isinstance(master, list):
                for v in master:
                    if isinstance(v, dict):
                        n = v.get("name", "")
                        if n:
                            master_names.add(n.lower().strip())
            
            real_names = set()
            if isinstance(real, dict):
                for v in real.values():
                    if isinstance(v, dict):
                        n = v.get("name", "")
                        if n:
                            real_names.add(n.lower().strip())
            elif isinstance(real, list):
                for v in real:
                    if isinstance(v, dict):
                        n = v.get("name", "")
                        if n:
                            real_names.add(n.lower().strip())
            
            overlap = master_names & real_names
            only_master = master_names - real_names
            only_real = real_names - master_names
            print(f"  重叠: {len(overlap)}人")
            print(f"  仅在master_10k: {len(only_master)}人 (前10: {list(only_master)[:10]})")
            print(f"  仅在real_people: {len(only_real)}人 (前10: {list(only_real)[:10]})")
        except Exception as e:
            print(f"  交叉验证失败: {e}")
