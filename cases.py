# -*- coding: utf-8 -*-
"""命例库：保存 / 读取 / 列表。存 json，一个命例一条。"""
import io
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "命例库.json")
DB_EXAMPLE = os.path.join(HERE, "命例库.example.json")


def _db():
    """真库优先，没有就用示例库（方便别人 clone 下来直接能跑）"""
    if os.path.exists(DB):
        return DB
    if os.path.exists(DB_EXAMPLE):
        return DB_EXAMPLE
    return DB


def _load():
    try:
        with io.open(_db(), "r", encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, list):
            return d
    except Exception:
        pass
    return []


def _save(items):
    with io.open(DB, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)


def all_cases():
    return _load()


def add_case(name, gender, year, month, day, hour, minute,
             longitude=114.06, true_solar=True, note="",
             day_gz="", month_gz="", year_gz="", hour_gz="",
             strength="", ge=""):
    """加一条；同名+同生日的覆盖，不重复堆"""
    items = _load()
    key = (name, year, month, day, hour, minute)
    items = [x for x in items
             if (x.get("name"), x.get("year"), x.get("month"),
                 x.get("day"), x.get("hour"), x.get("minute")) != key]
    items.append({
        "name": name, "gender": gender,
        "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute,
        "longitude": longitude, "true_solar": true_solar,
        "note": note,
        "pillars": "%s %s %s %s" % (year_gz, month_gz, day_gz, hour_gz),
        "strength": strength, "ge": ge,
        "saved": time.strftime("%Y-%m-%d %H:%M"),
    })
    _save(items)
    return len(items)


def del_case(name, year, month, day, hour, minute):
    items = _load()
    n0 = len(items)
    items = [x for x in items
             if (x.get("name"), x.get("year"), x.get("month"),
                 x.get("day"), x.get("hour"), x.get("minute")) !=
             (name, year, month, day, hour, minute)]
    _save(items)
    return n0 - len(items)
