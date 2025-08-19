from pm.db.models import engine, SessionLocal
from sqlalchemy import text
import time  # 추가: 재시도 로직을 위해 time 모듈 임포트


def get_duplicate_ids(session):
    """asset_id와 date 기준으로 중복인 경우, 가장 작은 id를 유지하고 나머지 id들을 수집합니다."""
    sql = text("""
        SELECT asset_id, date, MIN(id) AS keep_id, GROUP_CONCAT(id) AS all_ids, COUNT(*) AS cnt
        FROM prices
        GROUP BY asset_id, date
        HAVING COUNT(*) > 1
    """)
    result = session.execute(sql)
    duplicate_ids = []
    for row in result:
        ids = row.all_ids.split(',')
        keep_id = str(row.keep_id)
        # 가장 낮은 id(keep_id)를 제외한 나머지를 삭제 대상으로 추가합니다.
        for id in ids:
            if id != keep_id:
                duplicate_ids.append(int(id))
    return duplicate_ids


def delete_duplicate(session, dup_id, max_retries=3):
    """단일 중복 레코드를 삭제 시도하며, 실패 시 재시도 로직을 적용합니다."""
    for attempt in range(max_retries):
        try:
            session.execute(text("DELETE FROM prices WHERE id = :id"), {"id": dup_id})
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            if attempt < max_retries - 1:
                print(f"ID {dup_id} 삭제 중 오류 발생 (시도 {attempt+1}). 재시도 중...")
                time.sleep(2)  # 대기 후 재시도
            else:
                print(f"중복 레코드 ID {dup_id}를 삭제하는 데 실패했습니다: {e}")
                return False


def optimize_mysql_settings(session):
    """Optimize MySQL session settings to reduce lock wait timeouts and improve performance."""
    try:
        session.execute(text("SET SESSION innodb_lock_wait_timeout = 50"))
        session.execute(text("SET SESSION transaction_isolation = 'READ-COMMITTED'"))
        session.execute(text("SET SESSION group_concat_max_len = 1000000"))
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error optimizing MySQL settings: {e}")


def main():
    session = SessionLocal()
    try:
        optimize_mysql_settings(session)  # DB 설정 최적화 호출
        duplicate_ids = get_duplicate_ids(session)
        print(f"총 {len(duplicate_ids)}건의 중복 레코드가 발견되었습니다.")
        if duplicate_ids:
            success_count = 0
            for dup_id in duplicate_ids:
                if delete_duplicate(session, dup_id):
                    success_count += 1
            print(f"총 {len(duplicate_ids)}건 중 {success_count}건 삭제되었습니다.")
        else:
            print("삭제할 중복 레코드가 없습니다.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
