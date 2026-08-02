"""
Эталонный DAG для Airflow 3.x.

Пайплайн:
  1. get_blacklist            — читаем чёрный список из MSSQL (фильтр для дальнейших шагов);
  2. expand_links_clickhouse  — итеративный (BFS) поиск привязок в ClickHouse:
                                (idn1, t1) -> (idn2, t2) -> снова на вход -> ... до max_depth;
  3. resolve_sources          — агрегируем найденные пары и по агрегатам получаем из MSSQL
                                реестр источников (сервер / БД / процедура);
  4. check_sources            — параллельная проверка доступности источников (SELECT 1),
                                всё внутри ОДНОЙ таски через ThreadPoolExecutor;
  5. run_procedures           — параллельное выполнение процедур на доступных источниках,
                                тоже внутри одной таски (без взрыва количества тасков);
  6. aggregate_to_s3          — агрегация результатов по типу и запись parquet в S3.

Требуемые провайдеры / пакеты:
  apache-airflow-providers-microsoft-mssql
  apache-airflow-providers-amazon
  clickhouse-connect
  pandas, pyarrow, pymssql

Требуемые Airflow Connections:
  mssql_core     — «основной» MSSQL (чёрный список, реестр источников; login/password
                   из этого коннекта переиспользуются для динамических серверов);
  clickhouse_dwh — ClickHouse (host/port/login/password/schema);
  aws_s3         — S3/MinIO.

Airflow Variables (опционально, значения по умолчанию заданы ниже):
  link_seed_pairs   — JSON-список стартовых пар [[idn1, t1], ...]
  link_max_depth    — глубина обхода привязок
  s3_target_bucket  — бакет для выгрузки
"""

from __future__ import annotations

import io
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta

import pendulum

from airflow.sdk import dag, task, Variable  # Airflow 3.x SDK

log = logging.getLogger(__name__)

# ----------------------------- Константы ------------------------------------

MSSQL_CONN_ID = "mssql_core"
CLICKHOUSE_CONN_ID = "clickhouse_dwh"
S3_CONN_ID = "aws_s3"

DEFAULT_SEED_PAIRS = [[1001, "A"], [1002, "B"]]   # стартовые (idn1, t1)
DEFAULT_MAX_DEPTH = 3                             # глубина рекурсивного поиска
CH_BATCH_SIZE = 5_000                             # размер батча пар в одном запросе к CH
MAX_PARALLEL_SOURCES = 16                         # потоков для SELECT 1 / процедур
SOURCE_CHECK_TIMEOUT_SEC = 10
PROC_TIMEOUT_SEC = 600


# --------------------------- Вспомогательные --------------------------------

def _clickhouse_client():
    """Клиент ClickHouse на основе Airflow Connection."""
    import clickhouse_connect
    from airflow.hooks.base import BaseHook

    conn = BaseHook.get_connection(CLICKHOUSE_CONN_ID)
    return clickhouse_connect.get_client(
        host=conn.host,
        port=conn.port or 8123,
        username=conn.login or "default",
        password=conn.password or "",
        database=conn.schema or "default",
    )


def _mssql_dynamic_conn(server: str, database: str, timeout: int):
    """
    Прямое подключение pymssql к произвольному серверу из реестра источников.
    Логин/пароль берём из базового коннекта mssql_core (единая учётка сервиса).
    """
    import pymssql
    from airflow.hooks.base import BaseHook

    base = BaseHook.get_connection(MSSQL_CONN_ID)
    return pymssql.connect(
        server=server,
        user=base.login,
        password=base.password,
        database=database,
        timeout=timeout,
        login_timeout=timeout,
    )


# ------------------------------- DAG ----------------------------------------

@dag(
    dag_id="mssql_clickhouse_s3_pipeline",
    schedule="0 3 * * *",
    start_date=pendulum.datetime(2026, 1, 1, tz="Europe/Amsterdam"),
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "data-platform",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["mssql", "clickhouse", "s3", "reference"],
    doc_md=__doc__,
)
def mssql_clickhouse_s3_pipeline():

    # ------------------------------------------------------------------ 1 ----
    @task
    def get_blacklist() -> list[list]:
        """
        Чёрный список пар (idn, t) из MSSQL.
        Всё, что попало сюда, исключается из обхода привязок и из итоговых данных.
        """
        from airflow.providers.microsoft.mssql.hooks.mssql import MsSqlHook

        hook = MsSqlHook(mssql_conn_id=MSSQL_CONN_ID)
        rows = hook.get_records(
            """
            SELECT idn, t
            FROM dbo.blacklist WITH (NOLOCK)
            WHERE is_active = 1
            """
        )
        blacklist = [[r[0], r[1]] for r in rows]
        log.info("Чёрный список: %d записей", len(blacklist))
        return blacklist

    # ------------------------------------------------------------------ 2 ----
    @task(execution_timeout=timedelta(minutes=30))
    def expand_links_clickhouse(blacklist: list[list]) -> list[dict]:
        """
        Итеративный (BFS) поиск привязок в ClickHouse.

        Уровень 0: стартовые пары (idn1, t1).
        На каждом уровне выполняем ОДИН батчевый запрос:
            SELECT idn1, t1, idn2, t2
            FROM links
            WHERE (idn1, t1) IN (<пары текущего уровня>)
        Найденные (idn2, t2), которых ещё не видели и которых нет в чёрном
        списке, становятся входом следующего уровня. Так — до max_depth
        или пока не закончатся новые пары.
        """
        seed_pairs = json.loads(
            Variable.get("link_seed_pairs", default=json.dumps(DEFAULT_SEED_PAIRS))
        )
        max_depth = int(Variable.get("link_max_depth", default=DEFAULT_MAX_DEPTH))

        banned: set[tuple] = {tuple(p) for p in blacklist}
        visited: set[tuple] = set()
        frontier: set[tuple] = {tuple(p) for p in seed_pairs} - banned

        client = _clickhouse_client()
        edges: list[dict] = []

        for depth in range(max_depth):
            if not frontier:
                break

            next_frontier: set[tuple] = set()
            frontier_list = sorted(frontier)

            # Батчим, чтобы не собрать запрос-монстр при широком фронте обхода
            for i in range(0, len(frontier_list), CH_BATCH_SIZE):
                batch = frontier_list[i : i + CH_BATCH_SIZE]
                result = client.query(
                    """
                    SELECT idn1, t1, idn2, t2
                    FROM dwh.links
                    WHERE (idn1, t1) IN {pairs:Array(Tuple(Int64, String))}
                    """,
                    parameters={"pairs": batch},
                )
                for idn1, t1, idn2, t2 in result.result_rows:
                    child = (idn2, t2)
                    if child in banned:
                        continue
                    edges.append(
                        {"idn1": idn1, "t1": t1, "idn2": idn2, "t2": t2, "depth": depth}
                    )
                    if child not in visited and child not in frontier:
                        next_frontier.add(child)

            visited |= frontier
            frontier = next_frontier - visited
            log.info(
                "Уровень %d: найдено рёбер всего %d, новых пар для следующего уровня %d",
                depth, len(edges), len(frontier),
            )

        log.info("Обход завершён: %d рёбер, %d уникальных пар", len(edges), len(visited))
        return edges

    # ------------------------------------------------------------------ 3 ----
    @task
    def resolve_sources(edges: list[dict]) -> dict:
        """
        1) Агрегируем найденные привязки по (t2) — количество и список idn2;
        2) По агрегированным типам получаем из MSSQL реестр источников:
           сервер, база, процедура и параметры вызова.
        """
        import pandas as pd
        from airflow.providers.microsoft.mssql.hooks.mssql import MsSqlHook

        if not edges:
            log.warning("Привязки не найдены — источники запрашивать не для чего")
            return {"aggregates": [], "sources": []}

        df = pd.DataFrame(edges)
        agg = (
            df.groupby("t2")
            .agg(idn_list=("idn2", lambda s: sorted(set(s))), cnt=("idn2", "nunique"))
            .reset_index()
        )
        aggregates = agg.to_dict(orient="records")
        types = list(agg["t2"])

        hook = MsSqlHook(mssql_conn_id=MSSQL_CONN_ID)
        placeholders = ", ".join(["%s"] * len(types))
        rows = hook.get_records(
            f"""
            SELECT source_type, server_name, database_name, procedure_name
            FROM dbo.source_registry WITH (NOLOCK)
            WHERE is_active = 1
              AND source_type IN ({placeholders})
            """,
            parameters=types,
        )
        sources = [
            {
                "source_type": r[0],
                "server": r[1],
                "database": r[2],
                "procedure": r[3],
            }
            for r in rows
        ]
        log.info("Типов после агрегации: %d, источников в реестре: %d",
                 len(types), len(sources))
        return {"aggregates": aggregates, "sources": sources}

    # ------------------------------------------------------------------ 4 ----
    @task(execution_timeout=timedelta(minutes=10))
    def check_sources(resolved: dict) -> dict:
        """
        Параллельная проверка доступности всех источников через SELECT 1.
        Всё в одной таске: ThreadPoolExecutor вместо динамического маппинга,
        чтобы не плодить сотни тасков в UI.
        """
        sources = resolved["sources"]
        if not sources:
            return {**resolved, "sources": []}

        def ping(src: dict) -> tuple[dict, bool, str]:
            try:
                with _mssql_dynamic_conn(
                    src["server"], src["database"], SOURCE_CHECK_TIMEOUT_SEC
                ) as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT 1")
                        cur.fetchone()
                return src, True, "ok"
            except Exception as exc:  # noqa: BLE001 — фиксируем любую причину недоступности
                return src, False, str(exc)

        available, failed = [], []
        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_SOURCES) as pool:
            futures = [pool.submit(ping, s) for s in sources]
            for fut in as_completed(futures):
                src, ok, msg = fut.result()
                target = f"{src['server']}/{src['database']}"
                if ok:
                    log.info("Источник доступен: %s", target)
                    available.append(src)
                else:
                    log.warning("Источник НЕдоступен: %s — %s", target, msg)
                    failed.append({**src, "error": msg})

        if not available:
            raise RuntimeError("Ни один источник не доступен — пайплайн остановлен")
        if failed:
            log.warning("Недоступно источников: %d из %d", len(failed), len(sources))

        return {"aggregates": resolved["aggregates"], "sources": available}

    # ------------------------------------------------------------------ 5 ----
    @task(execution_timeout=timedelta(hours=1))
    def run_procedures(checked: dict) -> list[dict]:
        """
        Параллельное выполнение процедур на доступных источниках.
        Каждой процедуре передаём JSON со списком idn её типа (из агрегатов).
        Опять же — одна таска, параллелизм на уровне потоков.
        """
        sources = checked["sources"]
        agg_by_type = {a["t2"]: a for a in checked["aggregates"]}

        def run_one(src: dict) -> list[dict]:
            agg = agg_by_type.get(src["source_type"], {})
            idn_payload = json.dumps(agg.get("idn_list", []))
            proc = f"[{src['database']}].[dbo].[{src['procedure']}]"

            with _mssql_dynamic_conn(src["server"], src["database"], PROC_TIMEOUT_SEC) as conn:
                with conn.cursor(as_dict=True) as cur:
                    cur.execute(f"EXEC {proc} @idn_json = %s", (idn_payload,))
                    rows = cur.fetchall() or []

            for r in rows:  # помечаем происхождение каждой строки
                r["_source_type"] = src["source_type"]
                r["_source"] = f"{src['server']}/{src['database']}"
            log.info("Процедура %s на %s вернула %d строк",
                     src["procedure"], src["server"], len(rows))
            return rows

        results: list[dict] = []
        errors: list[str] = []
        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_SOURCES) as pool:
            futures = {pool.submit(run_one, s): s for s in sources}
            for fut in as_completed(futures):
                src = futures[fut]
                try:
                    results.extend(fut.result())
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{src['server']}/{src['procedure']}: {exc}")
                    log.error("Ошибка процедуры %s: %s", src["procedure"], exc)

        if errors and not results:
            raise RuntimeError("Все процедуры упали: " + "; ".join(errors))
        log.info("Итого строк со всех источников: %d (ошибок источников: %d)",
                 len(results), len(errors))
        return results

    # ------------------------------------------------------------------ 6 ----
    @task
    def aggregate_to_s3(rows: list[dict]) -> list[str]:
        """
        Агрегация результатов по типу источника и запись в S3:
        один parquet-файл на тип + общий summary.json.
        """
        import pandas as pd
        from airflow.providers.amazon.aws.hooks.s3 import S3Hook

        bucket = Variable.get("s3_target_bucket", default="data-exports")
        s3 = S3Hook(aws_conn_id=S3_CONN_ID)
        run_date = pendulum.now("UTC").format("YYYY-MM-DD")
        uploaded: list[str] = []

        if not rows:
            log.warning("Нет данных для выгрузки в S3")
            return uploaded

        df = pd.DataFrame(rows)
        for source_type, part in df.groupby("_source_type"):
            buf = io.BytesIO()
            part.drop(columns=["_source_type"]).to_parquet(buf, index=False)
            key = f"exports/{run_date}/type={source_type}/data.parquet"
            s3.load_bytes(buf.getvalue(), key=key, bucket_name=bucket, replace=True)
            uploaded.append(key)
            log.info("Записано s3://%s/%s (%d строк)", bucket, key, len(part))

        summary = (
            df.groupby("_source_type")
            .agg(rows=("_source", "size"), sources=("_source", "nunique"))
            .reset_index()
            .to_dict(orient="records")
        )
        summary_key = f"exports/{run_date}/summary.json"
        s3.load_string(
            json.dumps(summary, ensure_ascii=False, indent=2),
            key=summary_key, bucket_name=bucket, replace=True,
        )
        uploaded.append(summary_key)
        return uploaded

    # --------------------------- Граф зависимостей ---------------------------
    blacklist = get_blacklist()
    edges = expand_links_clickhouse(blacklist)
    resolved = resolve_sources(edges)
    checked = check_sources(resolved)
    proc_rows = run_procedures(checked)
    aggregate_to_s3(proc_rows)


mssql_clickhouse_s3_pipeline()
