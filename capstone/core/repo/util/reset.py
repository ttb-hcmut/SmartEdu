import argparse
import sqlite3

from core.repo.nosql.mongo_db import Mongo_DB

## usage: uv run python -m core.repo.util.reset [--no-keep-admin] [--course-trees] [--exercise-bank]

STUDENT_COLLECTIONS = ["students", "learning_trees", "learning_logs"]


def reset_sql(db_path: str = "core/repo/sql/student.db", keep_admin: bool = True):
    with sqlite3.connect(db_path) as conn:
        if keep_admin:
            conn.execute("DELETE FROM students WHERE is_admin = 0")
        else:
            conn.execute("DELETE FROM students")
        conn.commit()
    print(f"sql reset ({'admins kept' if keep_admin else 'all wiped'})")


def reset_mongo(course_trees: bool = False, exercise_bank: bool = False):
    mongo = Mongo_DB()
    targets = list(STUDENT_COLLECTIONS)
    if course_trees:
        targets.append("course_trees")
    if exercise_bank:
        targets.append("exercise_bank")
    existing = set(mongo.db.list_collection_names())
    for c in targets:
        if c in existing:
            mongo.db[c].drop()
            print(f"dropped {c}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-keep-admin", dest="keep_admin", action="store_false", default=True)
    ap.add_argument("--course-trees", action="store_true")
    ap.add_argument("--exercise-bank", action="store_true")
    args = ap.parse_args()
    reset_sql(keep_admin=args.keep_admin)
    reset_mongo(args.course_trees, args.exercise_bank)
    print("reset done")
