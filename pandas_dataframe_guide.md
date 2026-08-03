# Полный гайд по работе с DataFrame в pandas

> Актуально для **pandas 2.x** (проверено на 2.0–2.3). Отличия от 1.x отмечены отдельно.

---

## Оглавление

1. [Введение и установка](#1-введение-и-установка)
2. [Что такое DataFrame](#2-что-такое-dataframe)
3. [Создание DataFrame](#3-создание-dataframe)
4. [Атрибуты и структура](#4-атрибуты-и-структура)
5. [Просмотр и инспекция данных](#5-просмотр-и-инспекция-данных)
6. [Индексация и выборка данных](#6-индексация-и-выборка-данных)
7. [Булева фильтрация и query](#7-булева-фильтрация-и-query)
8. [Добавление, изменение и удаление](#8-добавление-изменение-и-удаление)
9. [Типы данных (dtypes)](#9-типы-данных-dtypes)
10. [Пропущенные значения](#10-пропущенные-значения)
11. [Дубликаты](#11-дубликаты)
12. [Сортировка](#12-сортировка)
13. [Применение функций](#13-применение-функций)
14. [Строковые операции (.str)](#14-строковые-операции-str)
15. [Дата и время (.dt)](#15-дата-и-время-dt)
16. [Категориальные данные](#16-категориальные-данные)
17. [GroupBy — группировка и агрегация](#17-groupby--группировка-и-агрегация)
18. [Сводные таблицы и реформатирование](#18-сводные-таблицы-и-реформатирование)
19. [Объединение таблиц](#19-объединение-таблиц)
20. [Оконные функции и сдвиги](#20-оконные-функции-и-сдвиги)
21. [Статистика и описательные метрики](#21-статистика-и-описательные-метрики)
22. [MultiIndex — иерархические индексы](#22-multiindex--иерархические-индексы)
23. [Временные ряды](#23-временные-ряды)
24. [Ввод-вывод (I/O)](#24-ввод-вывод-io)
25. [Визуализация](#25-визуализация)
26. [Стилизация (Styler)](#26-стилизация-styler)
27. [Настройки pandas](#27-настройки-pandas)
28. [Производительность и оптимизация](#28-производительность-и-оптимизация)
29. [Подводные камни и частые ошибки](#29-подводные-камни-и-частые-ошибки)
30. [Что нового в pandas 2.x](#30-что-нового-в-pandas-2x)
31. [Шпаргалка](#31-шпаргалка)

---

## 1. Введение и установка

### Установка

```bash
pip install pandas
```

С дополнительными зависимостями (Excel, Parquet, SQL, ускорения):

```bash
pip install "pandas[all]"
```

Точечно:

```bash
pip install pandas openpyxl pyarrow sqlalchemy numexpr bottleneck xlsxwriter
```

| Пакет | Зачем |
|---|---|
| `openpyxl` | чтение/запись `.xlsx` |
| `xlsxwriter` | продвинутая запись Excel (формат, графики) |
| `pyarrow` | Parquet, Feather, Arrow-бэкенд, быстрый CSV |
| `fastparquet` | альтернатива pyarrow для Parquet |
| `sqlalchemy` | работа с SQL-БД |
| `numexpr`, `bottleneck` | ускорение вычислений |
| `matplotlib` | `.plot()` |
| `lxml`, `html5lib`, `beautifulsoup4` | `read_html` |

### Стандартный импорт

```python
import pandas as pd
import numpy as np

print(pd.__version__)
pd.show_versions()          # полная диагностика окружения
```

---

## 2. Что такое DataFrame

`DataFrame` — двумерная таблица с помеченными осями:

* **ось 0 (`axis=0`, `index`)** — строки;
* **ось 1 (`axis=1`, `columns`)** — столбцы.

Каждый столбец — это `Series` (одномерный массив с индексом) со своим типом данных. Столбцы разных типов могут сосуществовать.

```
          columns →   name     age   salary
index ↓
  0                  'Анна'     28    120000
  1                  'Борис'    35    150000
  2                  'Вера'     42    180000
             dtype:  object    int64   int64
```

Ключевые свойства:

* **выравнивание по индексу** — операции между объектами автоматически сопоставляют строки/столбцы по меткам;
* **векторизация** — операции применяются ко всему столбцу сразу (быстро, без циклов);
* **иммутабельность dtype столбца** — тип общий на столбец, не на ячейку.

---

## 3. Создание DataFrame

### 3.1. Из словаря списков (самый частый способ)

```python
df = pd.DataFrame({
    "name":   ["Анна", "Борис", "Вера", "Глеб"],
    "age":    [28, 35, 42, 31],
    "city":   ["Москва", "СПб", "Москва", "Казань"],
    "salary": [120_000, 150_000, 180_000, 135_000],
})
```

### 3.2. Из списка словарей (записи / JSON-подобные данные)

```python
records = [
    {"name": "Анна",  "age": 28},
    {"name": "Борис", "age": 35, "city": "СПб"},   # недостающие → NaN
]
df = pd.DataFrame(records)
```

### 3.3. Из списка списков / кортежей

```python
data = [["Анна", 28], ["Борис", 35]]
df = pd.DataFrame(data, columns=["name", "age"])
```

### 3.4. Из NumPy-массива

```python
arr = np.random.default_rng(42).normal(size=(5, 3))
df = pd.DataFrame(arr, columns=list("ABC"), index=[f"r{i}" for i in range(5)])
```

### 3.5. Из Series

```python
s1 = pd.Series([1, 2, 3], name="a")
s2 = pd.Series([4, 5, 6], name="b")

df = pd.concat([s1, s2], axis=1)
df = pd.DataFrame({"a": s1, "b": s2})       # эквивалент
df = s1.to_frame()                           # одна Series → DataFrame
```

### 3.6. Из словаря Series (выравнивание по индексу!)

```python
d = {
    "a": pd.Series([1, 2, 3], index=["x", "y", "z"]),
    "b": pd.Series([10, 20],   index=["x", "y"]),   # z → NaN
}
df = pd.DataFrame(d)
```

### 3.7. Из структурированного массива и именованных кортежей

```python
from collections import namedtuple

Point = namedtuple("Point", "x y")
df = pd.DataFrame([Point(1, 2), Point(3, 4)])

rec = np.array([(1, "a"), (2, "b")], dtype=[("num", "i4"), ("ch", "U1")])
df = pd.DataFrame(rec)
```

### 3.8. Из файла

```python
df = pd.read_csv("data.csv")
df = pd.read_excel("data.xlsx", sheet_name="Лист1")
df = pd.read_json("data.json")
df = pd.read_parquet("data.parquet")
df = pd.read_sql("SELECT * FROM t", con)
df = pd.read_clipboard()          # из буфера обмена — удобно для быстрых тестов
```

### 3.9. Пустой DataFrame и типизированный скелет

```python
df = pd.DataFrame()
df = pd.DataFrame(columns=["a", "b", "c"])

# С заданными типами
df = pd.DataFrame({
    "a": pd.Series(dtype="int64"),
    "b": pd.Series(dtype="float64"),
    "c": pd.Series(dtype="datetime64[ns]"),
    "d": pd.Series(dtype="string"),
})
```

### 3.10. Синтетические данные для тестов

```python
rng = np.random.default_rng(0)

df = pd.DataFrame({
    "date":  pd.date_range("2024-01-01", periods=100, freq="D"),
    "cat":   rng.choice(list("ABC"), 100),
    "value": rng.normal(100, 15, 100).round(2),
    "qty":   rng.integers(1, 10, 100),
})
```

### 3.11. `from_dict` и `from_records`

```python
# orient="index" — ключи становятся строками
pd.DataFrame.from_dict(
    {"row1": [1, 2, 3], "row2": [4, 5, 6]},
    orient="index",
    columns=["a", "b", "c"],
)

# orient="tight" — полное описание с индексами и именами осей
pd.DataFrame.from_records(records, index="id")
```

### 3.12. Специальные конструкторы

```python
pd.date_range("2024-01-01", "2024-12-31", freq="MS")   # начала месяцев
pd.Index([1, 2, 3], name="id")
pd.MultiIndex.from_product([["A", "B"], [1, 2]], names=["g", "n"])
pd.RangeIndex(0, 100, 5)
```

---

## 4. Атрибуты и структура

```python
df.shape          # (n_rows, n_cols)
df.size           # общее число ячеек
df.ndim           # 2
df.columns        # Index столбцов
df.index          # Index строк
df.dtypes         # Series типов по столбцам
df.values         # numpy-массив (общий dtype — обычно object при смешении)
df.to_numpy()     # предпочтительнее .values
df.axes           # [index, columns]
df.empty          # True если 0 строк или 0 столбцов
df.flags          # флаги объекта
df.attrs          # словарь пользовательских метаданных (экспериментально)
```

### Работа с именами осей

```python
df.columns = ["a", "b", "c"]                       # переприсваивание
df.columns = df.columns.str.lower().str.strip()    # нормализация имён
df.index.name = "row_id"
df.columns.name = "feature"
df = df.rename_axis(index="id", columns="var")
```

### Индекс

```python
df.set_index("name")                       # столбец → индекс
df.set_index(["city", "name"])             # MultiIndex
df.set_index("name", drop=False)           # оставить столбец
df.reset_index()                           # индекс → столбец
df.reset_index(drop=True)                  # выбросить старый индекс
df.reindex([3, 2, 1, 0])                   # переупорядочить/расширить
df.reindex(columns=["c", "b", "a"])
df.reindex(index=full_range, fill_value=0)
df.sort_index()
df.index.is_unique
df.index.duplicated()
```

---

## 5. Просмотр и инспекция данных

```python
df.head()          # первые 5
df.head(20)
df.tail(3)
df.sample(5)                       # случайные 5 строк
df.sample(frac=0.1, random_state=1)
df.sample(n=3, replace=True, weights="salary")

df.info()                          # типы, non-null, память
df.info(memory_usage="deep")       # честная память для object
df.describe()                      # статистика по числовым
df.describe(include="all")         # все столбцы
df.describe(include=["object"])
df.describe(percentiles=[.01, .25, .5, .75, .99])

df.memory_usage(deep=True)
df.nunique()                       # число уникальных по столбцам
df.count()                         # число непустых
df["city"].unique()
df["city"].value_counts()
df["city"].value_counts(normalize=True)   # доли
df["city"].value_counts(dropna=False)
```

### Быстрая «карта» датасета

```python
def overview(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "dtype":     df.dtypes,
        "non_null":  df.notna().sum(),
        "nulls":     df.isna().sum(),
        "null_%":    (df.isna().mean() * 100).round(2),
        "nunique":   df.nunique(),
        "sample":    df.iloc[0] if len(df) else None,
    })

overview(df)
```

---

## 6. Индексация и выборка данных

### 6.1. Квадратные скобки `[]`

```python
df["age"]                 # Series (один столбец)
df[["age", "city"]]       # DataFrame (список столбцов)
df[0:3]                   # СРЕЗ ПО СТРОКАМ (позиционный)
df["a":"c"]               # срез по меткам индекса (включительно!)
df[df["age"] > 30]        # булева маска по строкам
```

> ⚠️ `[]` перегружен: скаляр/список → столбцы, срез/маска → строки. Для ясности используйте `.loc` / `.iloc`.

### 6.2. `.loc` — по меткам

```python
df.loc[0]                          # строка с меткой 0 → Series
df.loc[[0, 2, 4]]                  # несколько строк
df.loc[0:2]                        # срез ВКЛЮЧИТЕЛЬНО с обеих сторон
df.loc[:, "age"]                   # столбец
df.loc[:, "age":"salary"]          # срез столбцов включительно
df.loc[0, "age"]                   # скаляр
df.loc[0:2, ["name", "age"]]
df.loc[df["age"] > 30, "salary"]   # маска + столбец
df.loc[df["age"] > 30, ["name", "salary"]]
df.loc[lambda d: d["age"] > 30]    # callable — удобно в цепочках
df.loc[:, df.columns.str.startswith("s")]

# Присваивание
df.loc[df["age"] > 40, "senior"] = True
df.loc[0, "age"] = 29
df.loc["new_row"] = ["Дмитрий", 50, "Сочи", 200_000]   # добавление строки
```

### 6.3. `.iloc` — по позициям

```python
df.iloc[0]                 # первая строка
df.iloc[-1]                # последняя
df.iloc[0:3]               # срез, конец НЕ включается
df.iloc[:, 0]              # первый столбец
df.iloc[0, 1]              # ячейка
df.iloc[[0, 2], [1, 3]]
df.iloc[::2]               # каждая вторая строка
df.iloc[::-1]              # реверс
df.iloc[:, ::-1]           # реверс столбцов
df.iloc[np.r_[0:3, 10:13]] # несмежные диапазоны
```

### 6.4. `.at` / `.iat` — быстрый доступ к одной ячейке

```python
df.at[0, "age"]       # по меткам, быстрее .loc
df.iat[0, 1]          # по позициям, быстрее .iloc
df.at[0, "age"] = 30
```

### 6.5. Прочие способы

```python
df.get("age")                  # None, если нет столбца
df.get("nope", default=0)

df.filter(items=["age", "city"])
df.filter(like="sal")                  # подстрока в имени
df.filter(regex=r"^s.*y$")
df.filter(regex="^r", axis=0)          # по индексу

df.xs("Москва", level="city")          # срез MultiIndex
df.xs(("Москва", "Анна"), level=["city", "name"])

df.take([0, 2, 4])                     # позиционный отбор
df.take([0, 1], axis=1)

df.nlargest(3, "salary")
df.nsmallest(3, "age")
df.nlargest(3, ["salary", "age"])

df.first("3D")     # первые 3 дня (DatetimeIndex); в 2.1+ → df.loc[:cutoff]
df.head(0)         # только структура
```

### 6.6. `.pop`, `.squeeze`, `.item`

```python
col = df.pop("temp")        # извлечь и удалить столбец
df.squeeze()                # DataFrame 1×1 → скаляр, N×1 → Series
df.loc[df.id == 5, "x"].item()   # достать единственное значение
```

---

## 7. Булева фильтрация и query

### 7.1. Маски

```python
df[df["age"] > 30]
df[(df["age"] > 30) & (df["city"] == "Москва")]   # & | ~ и ОБЯЗАТЕЛЬНО скобки
df[~df["city"].isin(["Москва", "СПб"])]
df[df["name"].str.startswith("А")]
df[df["salary"].between(100_000, 160_000)]
df[df["city"].notna()]
df[df["age"].isna()]
df[df.isna().any(axis=1)]           # строки хоть с одним пропуском
df[df.notna().all(axis=1)]          # полностью заполненные строки
```

> `and` / `or` / `not` **не работают** с Series — используйте `&`, `|`, `~`.

### 7.2. `.query()` — фильтрация строкой

```python
df.query("age > 30")
df.query("age > 30 and city == 'Москва'")
df.query("city in ['Москва', 'СПб']")
df.query("salary > salary.mean()")
df.query("name.str.startswith('А')")
df.query("`total sum` > 100")                      # имена с пробелами — в бэктиках

threshold = 30
df.query("age > @threshold")                       # @ — переменная из окружения

df.query("age > 30", inplace=False, engine="numexpr")
```

Плюсы: читаемость, экономия памяти на больших данных.
Минусы: нет автодополнения/проверки типов, чуть медленнее на маленьких данных.

### 7.3. `.where()` / `.mask()` — замена вместо удаления

```python
df.where(df["age"] > 30)                 # не подошло → NaN, форма сохраняется
df["age"].where(df["age"] > 0, 0)        # отрицательные → 0
df["age"].mask(df["age"] > 100, np.nan)  # обратная логика
df.where(df > 0, other=-df)              # заменить на модуль
```

### 7.4. `np.where` и `np.select` — условные столбцы

```python
df["level"] = np.where(df["salary"] > 150_000, "high", "low")

conds = [df.salary < 130_000, df.salary < 170_000]
choices = ["junior", "middle"]
df["grade"] = np.select(conds, choices, default="senior")

# Pandas-нативно
df["grade"] = pd.cut(df["salary"],
                     bins=[0, 130_000, 170_000, np.inf],
                     labels=["junior", "middle", "senior"])
```

### 7.5. `isin` со словарём и DataFrame

```python
df.isin({"city": ["Москва"], "age": [28, 35]})   # поколоночно
df[df[["a", "b"]].isin([1, 2]).all(axis=1)]
```

---

## 8. Добавление, изменение и удаление

### 8.1. Столбцы

```python
df["bonus"] = df["salary"] * 0.1                 # новый столбец
df["const"] = 1                                   # broadcast
df["full"] = df["name"] + " (" + df["city"] + ")"

df.insert(1, "id", range(len(df)))                # вставка в позицию
df.insert(0, "flag", True, allow_duplicates=True)

# assign — не мутирует, возвращает копию (идеально для цепочек)
df2 = df.assign(
    bonus=lambda d: d.salary * 0.1,
    total=lambda d: d.salary + d.bonus,           # можно ссылаться на созданное выше
    year=2024,
)

# Удаление
df.drop(columns=["bonus"])
df.drop(columns=["a", "b"], errors="ignore")
df = df.drop("bonus", axis=1)
del df["bonus"]
col = df.pop("bonus")
```

### 8.2. Строки

```python
# Добавление
df.loc[len(df)] = ["Егор", 27, "Уфа", 110_000]
new = pd.DataFrame([{"name": "Егор", "age": 27}])
df = pd.concat([df, new], ignore_index=True)

# ⚠️ df.append() УДАЛЁН в pandas 2.0 — используйте pd.concat

# Удаление
df.drop(index=[0, 1])
df.drop(df[df["age"] < 18].index)
df.drop(labels=[0], axis=0)
df.truncate(before=2, after=5)
```

> Добавлять строки в цикле — антипаттерн (O(n²) копирований). Собирайте список словарей и делайте один `pd.DataFrame(...)` или `pd.concat`.

### 8.3. Переименование

```python
df.rename(columns={"old": "new", "a": "alpha"})
df.rename(index={0: "first"})
df.rename(columns=str.lower)
df.rename(columns=lambda c: c.strip().replace(" ", "_"))
df.rename(str.title, axis="columns")
df.set_axis(["a", "b", "c"], axis=1)
df.add_prefix("col_")
df.add_suffix("_2024")
```

### 8.4. Замена значений

```python
df.replace(0, np.nan)
df.replace([1, 2], [10, 20])
df.replace({"city": {"Мск": "Москва", "Спб": "СПб"}})
df.replace(r"^\s*$", np.nan, regex=True)          # пустые строки → NaN
df["x"].replace({np.nan: 0})
df.clip(lower=0, upper=100)                        # обрезка по границам
df["salary"].clip(upper=df["salary"].quantile(0.99))   # винзоризация
```

### 8.5. Изменение порядка столбцов

```python
df = df[["name", "city", "age", "salary"]]
df = df[sorted(df.columns)]

cols = ["id"] + [c for c in df.columns if c != "id"]
df = df[cols]

df = df.reindex(columns=desired_order)
```

---

## 9. Типы данных (dtypes)

### 9.1. Основные типы

| dtype | Описание | NaN-совместимость |
|---|---|---|
| `int64`, `int32`, `int8` | целые | нет (NaN превращает в float) |
| `float64`, `float32` | вещественные | да (`np.nan`) |
| `bool` | логический | нет |
| `object` | Python-объекты (обычно str) | да (`None`, `np.nan`) |
| `string` / `string[pyarrow]` | нативные строки | да (`pd.NA`) |
| `datetime64[ns]`, `datetime64[us]` | дата-время | да (`NaT`) |
| `timedelta64[ns]` | интервалы | да (`NaT`) |
| `category` | категории | да |
| `Int64`, `Int32` (заглавная I) | nullable целые | да (`pd.NA`) |
| `Float64` | nullable вещественные | да |
| `boolean` | nullable логический | да |
| `period[M]` | периоды | да |
| `interval` | интервалы значений | да |
| `Sparse[float]` | разреженный | да |
| `*[pyarrow]` | Arrow-бэкенд | да |

### 9.2. Приведение типов

```python
df["age"] = df["age"].astype("int32")
df = df.astype({"age": "int32", "salary": "float64", "city": "category"})
df["flag"] = df["flag"].astype(bool)

# Безопасное приведение с ошибками
pd.to_numeric(df["x"], errors="coerce")      # не-числа → NaN
pd.to_numeric(df["x"], errors="raise")       # исключение
pd.to_numeric(df["x"], downcast="integer")   # минимальный подходящий тип

pd.to_datetime(df["date"], errors="coerce", format="%d.%m.%Y")
pd.to_datetime(df["date"], dayfirst=True)
pd.to_timedelta(df["dur"], unit="s")

df.convert_dtypes()                          # авто-выбор лучших nullable типов
df.infer_objects()                           # попытка снять object
```

### 9.3. Nullable-типы (рекомендуются для новых проектов)

```python
s = pd.Series([1, 2, None], dtype="Int64")   # остаётся целым!
s.sum()          # 3
s.isna()         # [False, False, True]

df = df.astype({"count": "Int64", "name": "string", "ok": "boolean"})
```

### 9.4. Arrow-бэкенд (pandas 2.0+)

```python
df = pd.read_csv("data.csv", dtype_backend="pyarrow", engine="pyarrow")
df = df.convert_dtypes(dtype_backend="pyarrow")
s = pd.Series([1, 2, 3], dtype="int64[pyarrow]")
```

Плюсы: меньше памяти, быстрее строки, нативные NA, zero-copy с Parquet.

### 9.5. Отбор по типу

```python
df.select_dtypes(include="number")
df.select_dtypes(include=["int64", "float64"])
df.select_dtypes(include="object")
df.select_dtypes(exclude=["datetime64", "category"])
df.select_dtypes(include=np.number).columns.tolist()
```

---

## 10. Пропущенные значения

### 10.1. Обнаружение

```python
df.isna()                 # синоним isnull()
df.notna()
df.isna().sum()           # по столбцам
df.isna().sum(axis=1)     # по строкам
df.isna().mean()          # доля пропусков
df.isna().any()           # есть ли пропуски в столбце
df.isna().any().any()     # есть ли вообще
df.isna().sum().sum()     # всего пропусков

# Матрица пропусков (визуально)
df.isna().astype(int)
```

### 10.2. Удаление

```python
df.dropna()                              # строки с любым NaN
df.dropna(how="all")                     # только полностью пустые
df.dropna(subset=["age", "salary"])      # смотреть только на эти столбцы
df.dropna(thresh=3)                      # оставить строки с ≥3 непустыми
df.dropna(axis=1)                        # удалять столбцы
df.dropna(axis=1, thresh=len(df) * 0.7)  # столбцы с ≥70% заполнения
```

### 10.3. Заполнение

```python
df.fillna(0)
df.fillna({"age": df.age.median(), "city": "unknown"})
df["x"] = df["x"].fillna(df["x"].mean())

df.ffill()                     # протянуть вперёд (было fillna(method='ffill'))
df.bfill()                     # протянуть назад
df.ffill(limit=2)              # не более 2 подряд

# ⚠️ method= в fillna deprecated в 2.1 — используйте .ffill()/.bfill()

# Заполнение из другого DataFrame
df.fillna(df_other)
df.combine_first(df_other)     # приоритет у df, дырки — из df_other

# Групповое заполнение
df["salary"] = df.groupby("city")["salary"].transform(lambda s: s.fillna(s.median()))
```

### 10.4. Интерполяция

```python
df["x"].interpolate()                          # линейная
df["x"].interpolate(method="time")             # по DatetimeIndex
df["x"].interpolate(method="polynomial", order=2)
df["x"].interpolate(method="spline", order=3)
df["x"].interpolate(method="nearest")
df["x"].interpolate(limit_direction="both")
df["x"].interpolate(limit_area="inside")       # не экстраполировать края
```

### 10.5. Различия NaN / None / NaT / pd.NA

```python
np.nan        # float, NaN != NaN
None          # Python None, в object-столбцах
pd.NaT        # Not a Time, для datetime/timedelta
pd.NA         # универсальный NA для nullable-типов (kleene-логика)

pd.NA | True      # True
pd.NA & False     # False
np.nan == np.nan  # False  ← поэтому всегда .isna(), а не == np.nan
```

---

## 11. Дубликаты

```python
df.duplicated()                                # булева маска (True для повторов)
df.duplicated(subset=["name", "city"])
df.duplicated(keep="first")                    # по умолчанию
df.duplicated(keep="last")
df.duplicated(keep=False)                      # ВСЕ вхождения дублей

df.duplicated().sum()
df[df.duplicated(keep=False)].sort_values("name")   # посмотреть на дубли

df.drop_duplicates()
df.drop_duplicates(subset=["name"], keep="last")
df.drop_duplicates(ignore_index=True)

# Оставить самую свежую запись по ключу
(df.sort_values("updated_at")
   .drop_duplicates(subset="user_id", keep="last"))

# Уникальные значения
df["city"].unique()
df["city"].nunique()
df[["city", "dept"]].drop_duplicates()
```

---

## 12. Сортировка

```python
df.sort_values("age")
df.sort_values("age", ascending=False)
df.sort_values(["city", "age"], ascending=[True, False])
df.sort_values("age", na_position="first")
df.sort_values("name", key=lambda s: s.str.lower())   # регистронезависимо
df.sort_values("age", kind="mergesort")               # стабильная сортировка
df.sort_values("x", ignore_index=True)

df.sort_index()
df.sort_index(ascending=False)
df.sort_index(axis=1)                                  # сортировка столбцов
df.sort_index(level=["city", "name"])                  # MultiIndex

# Кастомный порядок через Categorical
order = ["low", "medium", "high"]
df["lvl"] = pd.Categorical(df["lvl"], categories=order, ordered=True)
df.sort_values("lvl")

# Ранги
df["rank"] = df["salary"].rank(ascending=False, method="dense")
# method: average (по умолчанию), min, max, first, dense
```

---

## 13. Применение функций

### 13.1. Векторизация — всегда предпочтительна

```python
df["total"] = df["price"] * df["qty"]                 # быстро
df["log"] = np.log1p(df["value"])
df["norm"] = (df.x - df.x.mean()) / df.x.std()
```

### 13.2. `.apply()`

```python
# По столбцам (axis=0, по умолчанию) — функция получает Series-столбец
df.apply(np.sum)
df.apply(lambda s: s.max() - s.min())

# По строкам (axis=1) — функция получает Series-строку. МЕДЛЕННО!
df.apply(lambda row: row["a"] * row["b"], axis=1)
df.apply(lambda r: f"{r['name']} из {r['city']}", axis=1)

# Возврат Series → расширение в несколько столбцов
df.apply(lambda r: pd.Series({"sum": r.a + r.b, "diff": r.a - r.b}), axis=1)

df.apply(func, args=(1, 2), extra_kw=3)
df.apply(func, raw=True)                 # передавать ndarray вместо Series (быстрее)
df.apply(func, result_type="expand")     # список → столбцы
```

### 13.3. `.map()` для Series

```python
df["city_code"] = df["city"].map({"Москва": 1, "СПб": 2})
df["city_code"] = df["city"].map({"Москва": 1}, na_action="ignore")
df["len"] = df["name"].map(len)
df["x"] = df["x"].map(lambda v: v ** 2)
```

### 13.4. `DataFrame.map()` — поэлементно (pandas 2.1+)

```python
df.map(lambda x: x * 2)                  # раньше назывался applymap
df.map("{:.2f}".format, na_action="ignore")
# df.applymap(...) — deprecated с 2.1
```

### 13.5. `.transform()` — форма сохраняется

```python
df.transform(lambda s: s / s.sum())
df[["a", "b"]].transform([np.sqrt, np.log])
df.transform({"a": np.sqrt, "b": "abs"})
```

### 13.6. `.pipe()` — цепочки

```python
def add_ratio(d, num, den):
    return d.assign(ratio=d[num] / d[den])

result = (
    df
    .query("age > 25")
    .pipe(add_ratio, "salary", "age")
    .sort_values("ratio", ascending=False)
    .head(10)
)
```

### 13.7. `.agg()` / `.aggregate()`

```python
df.agg("sum")
df.agg(["min", "max", "mean"])
df.agg({"age": ["min", "max"], "salary": "mean"})
df.agg(avg_age=("age", "mean"), tot=("salary", "sum"))   # named aggregation
```

### 13.8. `.eval()` — вычисления строкой

```python
df.eval("total = price * qty", inplace=True)
df.eval("margin = (revenue - cost) / revenue")
pd.eval("df1 + df2")                            # экономит память на больших данных
```

### 13.9. `np.vectorize` и `functools`

```python
f = np.vectorize(lambda a, b: a if a > b else b)
df["max"] = f(df["a"], df["b"])   # синтаксический сахар, НЕ ускорение
# Быстрее: df[["a","b"]].max(axis=1) или np.maximum(df.a, df.b)
```

**Иерархия скорости:** векторизация NumPy/pandas → `.map` со словарём → `.apply(axis=0)` → `.apply(axis=1)` → `iterrows()` (никогда).

---

## 14. Строковые операции (.str)

```python
s = df["name"]

# Регистр
s.str.lower(); s.str.upper(); s.str.title(); s.str.capitalize(); s.str.swapcase()
s.str.casefold()

# Очистка
s.str.strip(); s.str.lstrip(); s.str.rstrip()
s.str.strip(" .,")
s.str.replace(" ", "_", regex=False)
s.str.replace(r"\s+", " ", regex=True)
s.str.removeprefix("Mr. ")     # pandas 1.4+
s.str.removesuffix(".txt")

# Длина, срезы
s.str.len()
s.str[0]; s.str[:3]; s.str[-2:]
s.str.slice(0, 5, 2)
s.str.slice_replace(0, 3, "XXX")
s.str.pad(10, side="left", fillchar="0")
s.str.zfill(5)
s.str.center(20, "*")
s.str.wrap(30)

# Поиск
s.str.contains("ан", case=False, na=False)
s.str.contains(r"^\d+$", regex=True)
s.str.startswith("А"); s.str.endswith("а")
s.str.match(r"\d{3}-\d{2}")        # с начала строки
s.str.fullmatch(r"\d+")            # вся строка
s.str.find("а"); s.str.rfind("а")
s.str.count("а")

# Извлечение
s.str.extract(r"(\d{4})-(\d{2})")               # первая группа → столбцы
s.str.extract(r"(?P<year>\d{4})")               # именованные группы
s.str.extractall(r"(\d+)")                      # все совпадения → MultiIndex
s.str.findall(r"\d+")                           # список в ячейке

# Разбиение и склейка
s.str.split(",")                                # список
s.str.split(",", expand=True)                   # → DataFrame
s.str.split(",", n=1, expand=True)              # ограничить число разбиений
s.str.rsplit("/", n=1, expand=True)
s.str.partition("-")                            # 3 столбца: до, разделитель, после
s.str.cat(sep=", ")                             # склеить всю Series в строку
s.str.cat(df["city"], sep=" — ")                # поэлементная склейка
s.str.join("-")                                 # склеить списки внутри ячеек
s.str.get(0)                                    # элемент списка/символ

# Проверки
s.str.isnumeric(); s.str.isdigit(); s.str.isdecimal()
s.str.isalpha(); s.str.isalnum(); s.str.isspace()
s.str.islower(); s.str.isupper(); s.str.istitle()

# Кодировки и нормализация
s.str.encode("utf-8"); s.str.decode("utf-8")
s.str.normalize("NFKD")
s.str.translate(str.maketrans("ёЁ", "еЕ"))

# One-hot из строк со списками
s.str.get_dummies(sep="|")
```

### Практический пример: разбор адреса

```python
addr = pd.Series(["Москва, ул. Ленина, 12", "СПб, пр. Невский, 45"])

parts = addr.str.split(",", expand=True).apply(lambda c: c.str.strip())
parts.columns = ["city", "street", "house"]
parts["house"] = pd.to_numeric(parts["house"], errors="coerce")
```

---

## 15. Дата и время (.dt)

### 15.1. Парсинг

```python
df["date"] = pd.to_datetime(df["date"])
df["date"] = pd.to_datetime(df["date"], format="%d.%m.%Y")
df["date"] = pd.to_datetime(df["date"], format="mixed", dayfirst=True)   # 2.0+
df["date"] = pd.to_datetime(df["ts"], unit="s")            # unix timestamp
df["date"] = pd.to_datetime(df[["year", "month", "day"]])  # из столбцов
pd.to_datetime(df["d"], errors="coerce")                   # плохие → NaT
pd.to_datetime(df["d"], utc=True)
```

### 15.2. Компоненты

```python
d = df["date"].dt

d.year; d.month; d.day; d.hour; d.minute; d.second; d.microsecond
d.dayofweek        # 0=понедельник
d.day_name()       # 'Monday'
d.day_name(locale="ru_RU.utf8")
d.month_name()
d.quarter
d.dayofyear
d.days_in_month
d.is_month_start; d.is_month_end
d.is_quarter_start; d.is_year_end
d.is_leap_year
d.date; d.time
d.isocalendar()    # DataFrame: year, week, day
d.weekday
```

### 15.3. Округление и приведение

```python
d.normalize()              # обнулить время
d.round("h")               # до часа ('H' deprecated в 2.2 → 'h')
d.floor("D"); d.ceil("15min")
d.to_period("M")           # период-месяц
d.to_period("Q").astype(str)
d.strftime("%Y-%m")
d.tz_localize("Europe/Moscow")
d.tz_convert("UTC")
```

### 15.4. Арифметика

```python
df["date"] + pd.Timedelta(days=7)
df["date"] - pd.DateOffset(months=1)
df["date"] + pd.offsets.BMonthEnd()          # конец рабочего месяца
(df["end"] - df["start"]).dt.days
(df["end"] - df["start"]).dt.total_seconds() / 3600

# Возраст в полных годах
today = pd.Timestamp("2026-08-03")
df["age"] = (today - df["birth"]).dt.days // 365
```

### 15.5. Псевдонимы частот

| Алиас | Значение |
|---|---|
| `D` | календарный день |
| `B` | рабочий день |
| `W` / `W-MON` | неделя (с воскресенья / понедельника) |
| `ME` / `MS` | конец / начало месяца (в 2.2+; ранее `M`) |
| `QE` / `QS` | конец / начало квартала |
| `YE` / `YS` | конец / начало года |
| `h`, `min`, `s`, `ms`, `us`, `ns` | часы… наносекунды |
| `BME`, `BQE` | рабочие концы месяца/квартала |

---

## 16. Категориальные данные

```python
df["city"] = df["city"].astype("category")

c = df["city"].cat
c.categories
c.codes                      # целочисленные коды
c.rename_categories({"Мск": "Москва"})
c.add_categories(["Сочи"])
c.remove_categories(["СПб"])
c.remove_unused_categories()
c.reorder_categories(["Москва", "СПб"], ordered=True)
c.set_categories(["A", "B", "C"], ordered=True)
c.as_ordered(); c.as_unordered()

# Упорядоченные категории → можно сравнивать
sizes = pd.Categorical(["S", "L", "M"], categories=["S", "M", "L"], ordered=True)
sizes > "S"     # [False, True, True]

# Биннинг → категории
pd.cut(df["age"], bins=[0, 25, 40, 60, 100],
       labels=["юный", "молодой", "средний", "старший"])
pd.cut(df["age"], bins=4)                       # 4 равных интервала
pd.cut(df["x"], bins=[0, 1, 2], right=False, include_lowest=True)
pd.qcut(df["salary"], q=4, labels=["Q1", "Q2", "Q3", "Q4"])   # по квантилям
pd.qcut(df["salary"], q=10, duplicates="drop")
```

Экономия памяти: столбец из 1 млн строк с 5 уникальными значениями в `category` занимает в ~20 раз меньше.

---

## 17. GroupBy — группировка и агрегация

### 17.1. Базовое

```python
g = df.groupby("city")

g.size()                 # число строк в группе (включая NaN)
g.count()                # число непустых по каждому столбцу
g.sum(numeric_only=True)
g.mean(numeric_only=True)
g.median(); g.min(); g.max(); g.std(); g.var()
g.first(); g.last(); g.nth(0); g.nth([0, -1])
g.head(2)                # первые 2 строки КАЖДОЙ группы
g.tail(1)
g.ngroups
g.groups                 # dict: ключ → индексы
g.get_group("Москва")
g.nunique()
g.describe()
g.cumsum(); g.cumcount(); g.cummax()
g.rank()
g.sample(1)
g.idxmax()               # индекс максимума в каждой группе
```

### 17.2. Параметры `groupby`

```python
df.groupby("city", as_index=False)      # ключ остаётся столбцом
df.groupby("city", sort=False)          # не сортировать группы (быстрее)
df.groupby("city", dropna=False)        # NaN — отдельная группа
df.groupby("city", observed=True)       # для category: только встречающиеся
df.groupby(["city", "dept"])            # несколько ключей → MultiIndex
df.groupby(df["date"].dt.year)          # по вычисляемому ключу
df.groupby(level=0)                     # по уровню индекса
df.groupby(pd.Grouper(key="date", freq="ME"))   # по времени
df.groupby(lambda idx: idx % 2)         # по функции от индекса
df.groupby([df.a, df.b.str.lower()])
```

### 17.3. `.agg()` — гибкая агрегация

```python
# Одна функция ко всем столбцам
df.groupby("city").agg("mean", numeric_only=True)

# Несколько функций
df.groupby("city")["salary"].agg(["mean", "median", "std", "count"])

# Разные функции разным столбцам
df.groupby("city").agg({
    "salary": ["mean", "max"],
    "age":    "median",
    "name":   "count",
})

# Named aggregation — плоские понятные имена (РЕКОМЕНДУЕТСЯ)
df.groupby("city").agg(
    avg_salary=("salary", "mean"),
    max_salary=("salary", "max"),
    headcount=("name", "count"),
    salary_range=("salary", lambda s: s.max() - s.min()),
)

# Свои функции
def iqr(s):
    return s.quantile(.75) - s.quantile(.25)

df.groupby("city")["salary"].agg(iqr)
df.groupby("city")["salary"].agg([("IQR", iqr), ("CV", lambda s: s.std() / s.mean())])
```

Схлопывание MultiIndex в именах после agg:

```python
res = df.groupby("city").agg({"salary": ["mean", "max"]})
res.columns = ["_".join(c).strip("_") for c in res.columns]
res = res.reset_index()
```

### 17.4. `.transform()` — результат размера исходного DataFrame

```python
df["city_avg"] = df.groupby("city")["salary"].transform("mean")
df["dev"] = df["salary"] - df["city_avg"]
df["z"] = df.groupby("city")["salary"].transform(lambda s: (s - s.mean()) / s.std())
df["pct_of_city"] = df["salary"] / df.groupby("city")["salary"].transform("sum")
df["rn"] = df.groupby("city").cumcount() + 1        # нумерация внутри группы
```

### 17.5. `.filter()` — отбор целых групп

```python
df.groupby("city").filter(lambda g: len(g) >= 3)                  # группы ≥3 строк
df.groupby("city").filter(lambda g: g["salary"].mean() > 140_000)
```

### 17.6. `.apply()` — произвольная функция на группу

```python
# Топ-2 по зарплате в каждом городе
df.groupby("city", group_keys=False).apply(
    lambda g: g.nlargest(2, "salary")
)

# Возврат Series → DataFrame
df.groupby("city").apply(lambda g: pd.Series({
    "n": len(g),
    "spread": g.salary.max() - g.salary.min(),
}))

# ⚠️ В pandas 2.2+ apply на groupby включает ключи группировки — используйте
# include_groups=False, если функция их не должна видеть:
df.groupby("city").apply(lambda g: g["salary"].mean(), include_groups=False)
```

### 17.7. Итерация по группам

```python
for name, group in df.groupby("city"):
    print(name, len(group))

for (city, dept), group in df.groupby(["city", "dept"]):
    ...
```

### 17.8. Полезные рецепты

```python
# Доля каждой группы
df.groupby("city").size() / len(df)

# Топ-N категорий, остальное → "Other"
top = df["city"].value_counts().nlargest(5).index
df["city_grp"] = df["city"].where(df["city"].isin(top), "Other")

# Взвешенное среднее
df.groupby("city").apply(
    lambda g: np.average(g["price"], weights=g["qty"]),
    include_groups=False,
)

# Мода в группе
df.groupby("city")["dept"].agg(lambda s: s.mode().iat[0] if not s.mode().empty else None)

# Несколько столбцов после группировки, плоский результат
(df.groupby("city", as_index=False)
   .agg(n=("name", "size"), avg=("salary", "mean"))
   .sort_values("avg", ascending=False))
```

---

## 18. Сводные таблицы и реформатирование

### 18.1. `pivot_table` — агрегирующая сводная

```python
pd.pivot_table(
    df,
    values="salary",
    index="city",
    columns="dept",
    aggfunc="mean",
    fill_value=0,
    margins=True,               # строка/столбец «Всего»
    margins_name="Итого",
    dropna=True,
    observed=True,
)

# Несколько значений и функций
pd.pivot_table(df, values=["salary", "age"], index="city",
               aggfunc={"salary": ["mean", "sum"], "age": "median"})

df.pivot_table(index=["city", "dept"], columns="year", values="salary", aggfunc="sum")
```

### 18.2. `pivot` — реформат без агрегации

```python
df.pivot(index="date", columns="ticker", values="close")
df.pivot(index="id", columns="attr", values="val")
# ⚠️ Ошибка при дублирующихся парах (index, columns) — тогда pivot_table
```

### 18.3. `melt` — широкий → длинный

```python
pd.melt(
    df,
    id_vars=["id", "name"],
    value_vars=["jan", "feb", "mar"],
    var_name="month",
    value_name="amount",
    ignore_index=True,
)

df.melt(id_vars="id")        # остальные столбцы → в длинный формат
```

### 18.4. `stack` / `unstack`

```python
df.stack()                     # столбцы → уровень индекса (Series)
df.stack(future_stack=True)    # новое поведение pandas 2.1+
df.unstack()                   # уровень индекса → столбцы
df.unstack(level=0)
df.unstack(level="city", fill_value=0)

# Типичная связка
long = df.set_index(["date", "ticker"])["close"]
wide = long.unstack("ticker")
```

### 18.5. `crosstab` — таблица сопряжённости

```python
pd.crosstab(df["city"], df["dept"])
pd.crosstab(df["city"], df["dept"], normalize="index")    # доли по строкам
pd.crosstab(df["city"], df["dept"], values=df["salary"], aggfunc="mean")
pd.crosstab(df["city"], df["dept"], margins=True)
pd.crosstab([df.city, df.year], df.dept)
```

### 18.6. `explode` — список в ячейке → строки

```python
df = pd.DataFrame({"id": [1, 2], "tags": [["a", "b"], ["c"]]})
df.explode("tags")
df.explode(["tags", "scores"])       # синхронный explode нескольких (1.3+)
df.explode("tags", ignore_index=True)
```

### 18.7. `get_dummies` / `from_dummies` — one-hot

```python
pd.get_dummies(df, columns=["city"], prefix="c", drop_first=True, dtype=int)
pd.get_dummies(df["city"])
pd.from_dummies(dummies_df, sep="_")     # обратно (pandas 1.5+)
```

### 18.8. `wide_to_long`

```python
pd.wide_to_long(df, stubnames=["sales", "cost"], i="id", j="year", sep="_")
# столбцы sales_2020, sales_2021, cost_2020… → длинный формат
```

### 18.9. Транспонирование

```python
df.T
df.transpose()
```

---

## 19. Объединение таблиц

### 19.1. `pd.concat` — «склейка»

```python
pd.concat([df1, df2])                        # вертикально (axis=0)
pd.concat([df1, df2], ignore_index=True)
pd.concat([df1, df2], axis=1)                # горизонтально, по индексу
pd.concat([df1, df2], join="inner")          # только общие столбцы
pd.concat([df1, df2], keys=["A", "B"])       # добавить уровень индекса
pd.concat([df1, df2], keys=["a", "b"], names=["src", "row"])
pd.concat([df1, df2], verify_integrity=True) # ошибка при дублях индекса
pd.concat({"x": df1, "y": df2})              # словарь → keys автоматически
```

### 19.2. `pd.merge` — SQL-подобные JOIN

```python
pd.merge(left, right, on="id")                       # inner по умолчанию
pd.merge(left, right, on="id", how="left")
pd.merge(left, right, how="right")
pd.merge(left, right, how="outer")
pd.merge(left, right, how="cross")                   # декартово произведение (1.2+)

pd.merge(left, right, left_on="user_id", right_on="id")
pd.merge(left, right, left_index=True, right_index=True)
pd.merge(left, right, on=["a", "b"])                 # составной ключ
pd.merge(left, right, on="id", suffixes=("_l", "_r"))
pd.merge(left, right, on="id", indicator=True)       # столбец _merge
pd.merge(left, right, on="id", validate="one_to_many")  # проверка кардинальности

df.merge(other, on="id")                             # метод
```

`validate`: `"one_to_one"`, `"one_to_many"`, `"many_to_one"`, `"many_to_many"` — ловит неожиданное размножение строк.

Проверка качества соединения:

```python
m = left.merge(right, on="id", how="outer", indicator=True)
m["_merge"].value_counts()
# both / left_only / right_only
```

### 19.3. `.join` — по индексу

```python
left.join(right)                             # left join по индексу
left.join(right, how="inner")
left.join(right, on="key")                   # столбец left ↔ индекс right
left.join([df2, df3])                        # несколько сразу
left.join(right, lsuffix="_l", rsuffix="_r")
```

### 19.4. `merge_asof` — соединение по ближайшему ключу

```python
pd.merge_asof(
    trades.sort_values("time"),
    quotes.sort_values("time"),
    on="time",
    by="ticker",
    direction="backward",             # backward / forward / nearest
    tolerance=pd.Timedelta("2ms"),
)
```

### 19.5. `merge_ordered`

```python
pd.merge_ordered(df1, df2, on="date", by="group", fill_method="ffill")
```

### 19.6. `combine_first` и `update`

```python
df1.combine_first(df2)          # дырки в df1 заполнить из df2
df1.update(df2)                 # ⚠️ мутирует df1 на месте
df1.combine(df2, np.maximum)    # поэлементная функция
```

### 19.7. `compare` — различия между таблицами

```python
df1.compare(df2)
df1.compare(df2, align_axis=0, keep_shape=True, keep_equal=True)
df1.equals(df2)                          # полное совпадение (NaN == NaN здесь True)
pd.testing.assert_frame_equal(df1, df2)  # для тестов, с допусками
```

---

## 20. Оконные функции и сдвиги

### 20.1. Сдвиги и разности

```python
df["prev"] = df["value"].shift(1)
df["next"] = df["value"].shift(-1)
df["prev_day"] = df["value"].shift(freq="D")       # сдвиг по времени
df["diff"] = df["value"].diff()
df["diff2"] = df["value"].diff(2)
df["pct"] = df["value"].pct_change()
df["pct_yoy"] = df["value"].pct_change(periods=12)

# Внутри групп
df["prev_in_grp"] = df.groupby("id")["value"].shift(1)
```

### 20.2. `rolling` — скользящее окно

```python
df["ma7"] = df["value"].rolling(7).mean()
df["ma7"] = df["value"].rolling(7, min_periods=1).mean()
df["ma"] = df["value"].rolling(window=7, center=True).mean()
df["std"] = df["value"].rolling(30).std()
df["mx"] = df["value"].rolling(5).max()
df["q90"] = df["value"].rolling(20).quantile(0.9)
df["cust"] = df["value"].rolling(5).apply(lambda a: a[-1] - a[0], raw=True)

# Окно по времени (нужен DatetimeIndex)
df.set_index("date")["value"].rolling("7D").mean()
df.set_index("date")["value"].rolling("30D", closed="left").sum()

# Взвешенное окно
df["value"].rolling(5, win_type="gaussian").mean(std=1)

# Корреляция/ковариация в окне
df["a"].rolling(30).corr(df["b"])
df["a"].rolling(30).cov(df["b"])

# По группам
df.groupby("id")["value"].rolling(7).mean().reset_index(level=0, drop=True)
```

### 20.3. `expanding` — накопительное окно

```python
df["cummean"] = df["value"].expanding().mean()
df["cummax"] = df["value"].expanding(min_periods=3).max()
```

### 20.4. `ewm` — экспоненциальное сглаживание

```python
df["ema"] = df["value"].ewm(span=10, adjust=False).mean()
df["ema"] = df["value"].ewm(alpha=0.3).mean()
df["ema"] = df["value"].ewm(halflife="7D", times=df["date"]).mean()
df["evol"] = df["value"].ewm(span=20).std()
```

### 20.5. Кумулятивные функции

```python
df["value"].cumsum()
df["value"].cumprod()
df["value"].cummax()
df["value"].cummin()
df.groupby("id")["value"].cumsum()

# Drawdown
cum = (1 + df["ret"]).cumprod()
df["dd"] = cum / cum.cummax() - 1
```

---

## 21. Статистика и описательные метрики

```python
df.sum(); df.mean(); df.median(); df.mode()
df.min(); df.max(); df.std(); df.var(); df.sem()
df.prod(); df.count()
df.quantile(0.5)
df.quantile([.1, .5, .9])
df.skew(); df.kurt()
df.abs(); df.round(2)
df.idxmax(); df.idxmin()
df.cumsum(); df.cumprod()
df.pct_change()
df.diff()
df.rank()
df.clip(0, 100)
df.mad()                     # ⚠️ удалено в 2.0 → (df - df.mean()).abs().mean()

df.sum(axis=1)               # по строкам
df.mean(numeric_only=True)   # игнорировать нечисловые
df.sum(skipna=False)         # не игнорировать NaN
df.sum(min_count=1)          # пустая сумма → NaN, а не 0

df.corr()                    # Пирсон
df.corr(method="spearman")
df.corr(method="kendall")
df.corr(numeric_only=True)
df["a"].corr(df["b"])
df.corrwith(other_df)
df.cov()

df.any(); df.all()
df.all(axis=1)

df.value_counts()            # по всем столбцам сразу (1.1+)
df[["a", "b"]].value_counts(normalize=True)
```

### Быстрый профиль числового столбца

```python
s = df["salary"]
pd.Series({
    "count": s.count(), "mean": s.mean(), "std": s.std(),
    "min": s.min(), "p25": s.quantile(.25), "p50": s.median(),
    "p75": s.quantile(.75), "max": s.max(),
    "skew": s.skew(), "nulls": s.isna().sum(),
})
```

---

## 22. MultiIndex — иерархические индексы

### 22.1. Создание

```python
df.set_index(["city", "dept"])

pd.MultiIndex.from_tuples([("A", 1), ("B", 2)], names=["g", "n"])
pd.MultiIndex.from_product([["A", "B"], [1, 2]], names=["g", "n"])
pd.MultiIndex.from_arrays([["A", "A", "B"], [1, 2, 1]])
pd.MultiIndex.from_frame(df[["city", "dept"]])
```

### 22.2. Выборка

```python
mi = df.set_index(["city", "dept"]).sort_index()

mi.loc["Москва"]                       # весь блок
mi.loc[("Москва", "IT")]
mi.loc[("Москва", "IT"), "salary"]
mi.loc[["Москва", "СПб"]]
mi.loc[(slice(None), "IT"), :]         # все города, dept=IT
mi.loc[pd.IndexSlice[:, "IT"], :]      # то же, читаемее

idx = pd.IndexSlice
mi.loc[idx["Москва":"СПб", ["IT", "HR"]], :]

mi.xs("IT", level="dept")
mi.xs("IT", level="dept", drop_level=False)
```

> Для срезов MultiIndex обязательно `sort_index()`, иначе `UnsortedIndexError` / деградация производительности.

### 22.3. Работа с уровнями

```python
mi.index.names
mi.index.levels
mi.index.get_level_values("city")
mi.index.get_level_values(0)

mi.droplevel(0)
mi.swaplevel(0, 1).sort_index()
mi.reorder_levels(["dept", "city"])
mi.reset_index(level="dept")
mi.rename_axis(index=["CITY", "DEPT"])

mi.groupby(level="city").sum()
mi.sum(level="city")            # ⚠️ удалено в 2.0 → groupby(level=...)
```

### 22.4. Многоуровневые столбцы

```python
df.columns = pd.MultiIndex.from_tuples([("info", "name"), ("info", "age"),
                                        ("pay", "salary")])
df["info"]
df[("info", "age")]
df.loc[:, ("pay", slice(None))]

# Схлопывание
df.columns = ["_".join(filter(None, c)) for c in df.columns]
```

---

## 23. Временные ряды

```python
ts = df.set_index("date").sort_index()

# Срезы по строкам дат
ts["2024"]
ts["2024-03"]
ts["2024-01":"2024-06"]
ts.loc["2024-01-15":"2024-02-01"]
ts.between_time("09:00", "18:00")
ts.at_time("12:00")

# Ресемплинг
ts.resample("ME").sum()
ts.resample("W-MON").mean()
ts.resample("QE").agg({"sales": "sum", "price": "mean"})
ts.resample("D").ffill()               # апсемплинг с протяжкой
ts.resample("h").interpolate()
ts.resample("ME", closed="left", label="left").sum()
ts.resample("ME").ohlc()               # open/high/low/close

# Сдвиг всего ряда
ts.shift(1, freq="D")
ts.tshift(1)                           # ⚠️ удалён в 2.0

# Частота и заполнение пропусков в датах
ts.asfreq("D")
ts.asfreq("D", method="ffill")
full = pd.date_range(ts.index.min(), ts.index.max(), freq="D")
ts = ts.reindex(full).ffill()

# Часовые пояса
ts.tz_localize("Europe/Moscow").tz_convert("UTC")

# Периоды
ts.to_period("M")
ts.to_timestamp()

# Скользящие метрики по времени
ts["value"].rolling("30D").mean()
```

### Пример: месячная динамика с YoY

```python
monthly = (
    df.set_index("date")
      .resample("ME")["revenue"].sum()
      .to_frame("revenue")
      .assign(
          mom=lambda d: d.revenue.pct_change(),
          yoy=lambda d: d.revenue.pct_change(12),
          ma3=lambda d: d.revenue.rolling(3).mean(),
      )
)
```

---

## 24. Ввод-вывод (I/O)

### 24.1. CSV

```python
# Чтение
df = pd.read_csv("data.csv")
df = pd.read_csv(
    "data.csv",
    sep=";",                    # разделитель (sep=None + engine='python' → автоопределение)
    decimal=",",                # десятичный разделитель
    encoding="utf-8",           # или "cp1251", "utf-8-sig"
    header=0,                   # строка заголовка; None — нет заголовка
    names=["a", "b", "c"],      # свои имена
    index_col="id",
    usecols=["a", "b"],         # только нужные столбцы — экономия памяти
    usecols=lambda c: not c.startswith("tmp"),
    dtype={"id": "int32", "code": "string"},
    parse_dates=["date"],
    date_format="%d.%m.%Y",     # pandas 2.0+
    na_values=["", "NA", "-", "н/д"],
    keep_default_na=True,
    skiprows=3,
    skiprows=lambda i: i % 2 == 1,
    nrows=1000,
    skipfooter=2,               # требует engine="python"
    thousands=" ",
    comment="#",
    true_values=["да"], false_values=["нет"],
    converters={"price": lambda x: float(x.replace(",", "."))},
    on_bad_lines="skip",        # "error" | "warn" | "skip"
    low_memory=False,
    engine="pyarrow",           # быстрый парсер (2.0+)
    dtype_backend="pyarrow",
    compression="gzip",         # infer по умолчанию
    chunksize=100_000,          # итератор по частям
)

# Запись
df.to_csv("out.csv", index=False)
df.to_csv("out.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig")
df.to_csv("out.csv", columns=["a", "b"], float_format="%.2f", na_rep="")
df.to_csv("out.csv.gz", compression="gzip")
csv_str = df.to_csv(index=False)            # в строку
```

> `encoding="utf-8-sig"` — чтобы Excel корректно открыл кириллицу.

Чтение большого файла по частям:

```python
total = 0
for chunk in pd.read_csv("huge.csv", chunksize=500_000):
    total += chunk.query("amount > 0")["amount"].sum()
```

### 24.2. Excel

```python
df = pd.read_excel("f.xlsx", sheet_name="Лист1")
df = pd.read_excel("f.xlsx", sheet_name=0)
dfs = pd.read_excel("f.xlsx", sheet_name=None)       # dict всех листов
dfs = pd.read_excel("f.xlsx", sheet_name=["A", "B"])
df = pd.read_excel("f.xlsx", skiprows=4, usecols="B:F", header=1, engine="openpyxl")

df.to_excel("out.xlsx", index=False, sheet_name="Данные")
df.to_excel("out.xlsx", startrow=2, startcol=1, freeze_panes=(1, 0))

# Несколько листов
with pd.ExcelWriter("out.xlsx", engine="xlsxwriter") as w:
    df1.to_excel(w, sheet_name="Продажи", index=False)
    df2.to_excel(w, sheet_name="Клиенты", index=False)

    wb, ws = w.book, w.sheets["Продажи"]
    money = wb.add_format({"num_format": "#,##0.00"})
    ws.set_column("C:C", 14, money)
    ws.autofilter(0, 0, len(df1), len(df1.columns) - 1)

# Дозапись в существующий файл
with pd.ExcelWriter("out.xlsx", mode="a", engine="openpyxl",
                    if_sheet_exists="replace") as w:
    df3.to_excel(w, sheet_name="Новый")
```

### 24.3. JSON

```python
df = pd.read_json("d.json")
df = pd.read_json("d.json", orient="records", lines=True)   # JSON Lines
df = pd.read_json("d.json", convert_dates=["date"])

df.to_json("out.json", orient="records", force_ascii=False, indent=2)
df.to_json("out.jsonl", orient="records", lines=True)
df.to_json(orient="split", date_format="iso")

# Вложенный JSON
from pandas import json_normalize
json_normalize(data, record_path="items", meta=["id", ["user", "name"]],
               sep="_", errors="ignore")
```

`orient`: `records`, `split`, `index`, `columns`, `values`, `table`.

### 24.4. Parquet / Feather / ORC

```python
df.to_parquet("d.parquet", engine="pyarrow", compression="snappy", index=False)
df.to_parquet("data/", partition_cols=["year", "month"])
df = pd.read_parquet("d.parquet", columns=["a", "b"])
df = pd.read_parquet("data/", filters=[("year", "=", 2024)])

df.to_feather("d.feather")
df = pd.read_feather("d.feather")

df.to_orc("d.orc")
```

Parquet — лучший формат для промежуточного хранения: типы сохраняются, файлы в разы меньше, чтение быстрее CSV на порядок.

### 24.5. SQL

```python
from sqlalchemy import create_engine

engine = create_engine("postgresql+psycopg2://user:pass@host:5432/db")

df = pd.read_sql("SELECT * FROM sales WHERE year = %(y)s", engine, params={"y": 2024})
df = pd.read_sql_table("sales", engine, columns=["id", "amount"])
df = pd.read_sql_query("SELECT ...", engine, parse_dates=["date"], chunksize=50_000)

df.to_sql("sales", engine, if_exists="append", index=False,
          chunksize=10_000, method="multi",
          dtype={"amount": sqlalchemy.types.Numeric(12, 2)})
# if_exists: "fail" | "replace" | "append"

# SQLite без SQLAlchemy
import sqlite3
with sqlite3.connect("local.db") as con:
    df.to_sql("t", con, if_exists="replace", index=False)
    out = pd.read_sql("SELECT * FROM t", con)
```

### 24.6. Прочие форматы

```python
pd.read_html("https://example.com/page")     # список таблиц со страницы
df.to_html("out.html", index=False, classes="table", escape=False)

pd.read_clipboard()
df.to_clipboard(index=False)

df.to_markdown(index=False)                  # нужен tabulate
df.to_latex(index=False)
df.to_string(max_rows=20)
df.to_dict(orient="records")                 # records/list/dict/series/split/index/tight
df.to_numpy()
df.to_pickle("d.pkl"); pd.read_pickle("d.pkl")
df.to_xml("d.xml"); pd.read_xml("d.xml")
pd.read_stata(...); pd.read_sas(...); pd.read_spss(...); pd.read_hdf(...)
pd.read_fwf("fixed.txt", widths=[10, 5, 20])
```

---

## 25. Визуализация

```python
import matplotlib.pyplot as plt

df.plot()                                       # линии по всем числовым
df.plot(x="date", y="value", figsize=(12, 5), title="Динамика")
df.plot(kind="bar", stacked=True)
df.plot.barh()
df.plot.hist(bins=30, alpha=0.6)
df.plot.box()
df.plot.kde()
df.plot.area()
df.plot.scatter(x="age", y="salary", c="salary", colormap="viridis", s=50)
df.plot.pie(y="share", autopct="%1.1f%%")
df.plot.hexbin(x="a", y="b", gridsize=25)

df.plot(subplots=True, layout=(2, 2), figsize=(12, 8), sharex=False)
df.plot(secondary_y=["rate"])
df.plot(logy=True, grid=True, rot=45, xlim=(0, 100))

pd.plotting.scatter_matrix(df, figsize=(10, 10), diagonal="kde")
pd.plotting.autocorrelation_plot(df["value"])
pd.plotting.lag_plot(df["value"])
pd.plotting.parallel_coordinates(df, "class")

ax = df.plot(...)
ax.set_ylabel("₽")
plt.tight_layout()
plt.savefig("chart.png", dpi=150)
plt.show()

# Другой бэкенд
pd.options.plotting.backend = "plotly"
df.plot(x="date", y="value")
```

---

## 26. Стилизация (Styler)

```python
(df.style
   .format({"salary": "{:,.0f} ₽", "rate": "{:.1%}"})
   .background_gradient(subset=["salary"], cmap="RdYlGn")
   .bar(subset=["qty"], color="#5fba7d")
   .highlight_max(subset=["salary"], color="lightgreen")
   .highlight_min(subset=["salary"], color="salmon")
   .highlight_null(color="lightgray")
   .set_caption("Зарплаты по сотрудникам")
   .set_properties(**{"text-align": "center"})
   .hide(axis="index")
   .applymap(lambda v: "color: red" if v < 0 else "", subset=["profit"])
   .apply(lambda s: ["font-weight: bold" if v == s.max() else "" for v in s])
)

styled.to_excel("styled.xlsx", engine="openpyxl")
styled.to_html("styled.html")
```

---

## 27. Настройки pandas

```python
pd.set_option("display.max_rows", 200)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)
pd.set_option("display.max_colwidth", 100)
pd.set_option("display.float_format", "{:,.2f}".format)
pd.set_option("display.precision", 3)
pd.set_option("mode.copy_on_write", True)          # рекомендуется в 2.x
pd.set_option("future.no_silent_downcasting", True)

pd.get_option("display.max_rows")
pd.reset_option("display.max_rows")
pd.reset_option("all")
pd.describe_option("display")

# Временно
with pd.option_context("display.max_rows", 1000, "display.max_columns", 50):
    display(df)
```

---

## 28. Производительность и оптимизация

### 28.1. Память

```python
df.memory_usage(deep=True).sum() / 1024**2      # МБ

def downcast(df):
    for c in df.select_dtypes("integer"):
        df[c] = pd.to_numeric(df[c], downcast="integer")
    for c in df.select_dtypes("float"):
        df[c] = pd.to_numeric(df[c], downcast="float")
    for c in df.select_dtypes("object"):
        if df[c].nunique() / len(df) < 0.5:
            df[c] = df[c].astype("category")
    return df
```

### 28.2. Что действительно ускоряет

| Приём | Эффект |
|---|---|
| Векторизация вместо `apply(axis=1)` | 10–1000× |
| `category` для строк с малой кардинальностью | ×5–50 память |
| `usecols` / `columns` при чтении | линейно |
| Parquet вместо CSV | 5–20× чтение |
| `engine="pyarrow"` в `read_csv` | 2–10× |
| `sort=False` в `groupby` | 10–30% |
| `.map(dict)` вместо `.apply(lambda)` | 5–20× |
| `df.to_numpy()` для тяжёлой математики | 2–5× |
| `numexpr` + `.eval()` на больших выражениях | 2–4× |
| `merge` по индексу вместо столбца | 1.5–3× |

### 28.3. Антипаттерны

```python
# ❌ Никогда
for i, row in df.iterrows():
    df.loc[i, "y"] = row["a"] * 2

# ✅
df["y"] = df["a"] * 2

# ❌ Рост в цикле — O(n²)
out = pd.DataFrame()
for x in items:
    out = pd.concat([out, process(x)])

# ✅
out = pd.concat([process(x) for x in items], ignore_index=True)

# ❌ Цепочка индексаций
df[df.a > 0]["b"] = 1

# ✅
df.loc[df.a > 0, "b"] = 1
```

### 28.4. Профилирование

```python
%timeit df["a"] * 2
%%time
%prun df.groupby("k").sum()
%memit df.copy()
```

### 28.5. Когда pandas мало

* **Polars** — быстрее в 5–30×, ленивые запросы, отличная многопоточность.
* **DuckDB** — SQL прямо по DataFrame/Parquet, не грузит всё в память.
* **Dask** / **Modin** — распараллеливание с почти тем же API.
* **PyArrow** — работа с колоночными данными без pandas.

```python
import duckdb
duckdb.sql("SELECT city, avg(salary) FROM df GROUP BY city").df()
```

---

## 29. Подводные камни и частые ошибки

### 29.1. `SettingWithCopyWarning`

```python
# ❌ Chained indexing — неизвестно, копия или вид
sub = df[df.age > 30]
sub["flag"] = 1                # предупреждение, изменение может не попасть в df

# ✅ Явная копия
sub = df[df.age > 30].copy()
sub["flag"] = 1

# ✅ Одна операция .loc
df.loc[df.age > 30, "flag"] = 1
```

В pandas 2.x включите Copy-on-Write — предупреждение исчезает, семантика становится предсказуемой:

```python
pd.set_option("mode.copy_on_write", True)
```

### 29.2. `inplace=True` — не даёт выигрыша и ломает цепочки

```python
# ❌
df.drop(columns=["x"], inplace=True)

# ✅
df = df.drop(columns=["x"])
```

`inplace` внутри всё равно часто делает копию, а при Copy-on-Write считается устаревшим подходом.

### 29.3. Сравнение с NaN

```python
df[df.x == np.nan]     # ❌ всегда пусто
df[df.x.isna()]        # ✅
```

### 29.4. Логические операторы

```python
df[df.a > 0 and df.b > 0]        # ❌ ValueError
df[(df.a > 0) & (df.b > 0)]      # ✅
```

### 29.5. Целые числа «портятся» в float

```python
pd.Series([1, 2, None])                  # float64: 1.0, 2.0, NaN
pd.Series([1, 2, None], dtype="Int64")   # ✅ Int64: 1, 2, <NA>
```

### 29.6. Срезы `.loc` включительны

```python
df.loc[0:2]     # 3 строки: 0, 1, 2
df.iloc[0:2]    # 2 строки: 0, 1
```

### 29.7. Индекс после фильтрации не сбрасывается

```python
sub = df[df.a > 0]           # индексы «дырявые»
sub.iloc[0]                  # первая строка
sub.loc[0]                   # KeyError, если 0 отфильтрован
sub = sub.reset_index(drop=True)
```

### 29.8. Дубликаты столбцов

```python
df.columns.duplicated().any()
df = df.loc[:, ~df.columns.duplicated()]
```

### 29.9. `merge` размножает строки

```python
before = len(left)
res = left.merge(right, on="id", how="left", validate="many_to_one")
assert len(res) == before
```

### 29.10. Плавающая точка

```python
0.1 + 0.2 == 0.3                    # False
np.isclose(0.1 + 0.2, 0.3)          # True
df.round(2)
```

### 29.11. Что удалено/изменено в pandas 2.0+

| Было | Стало |
|---|---|
| `df.append(...)` | `pd.concat([...])` |
| `df.applymap(...)` | `df.map(...)` |
| `fillna(method="ffill")` | `df.ffill()` |
| `df.sum(level=...)` | `df.groupby(level=...).sum()` |
| `df.mad()` | `(df - df.mean()).abs().mean()` |
| `pd.np` | `import numpy as np` |
| `freq="M"`, `"H"`, `"T"` | `"ME"`, `"h"`, `"min"` |
| `df.iteritems()` | `df.items()` |
| `df.lookup()` | `df.melt` + `merge` или `numpy` |
| `pd.Timestamp.freq` | убрано |

---

## 30. Что нового в pandas 2.x

1. **Arrow-бэкенд** — `dtype_backend="pyarrow"`: меньше памяти, быстрее строки, нативные NA.
2. **Copy-on-Write** — предсказуемая семантика копий, меньше лишних копирований; станет поведением по умолчанию в pandas 3.0.
3. **Нестандартное разрешение времени** — `datetime64[s]`, `[ms]`, `[us]`, а не только `[ns]` (шире диапазон дат).
4. **`engine="pyarrow"` в `read_csv`** — многопоточный парсинг.
5. **Named aggregation** и `include_groups` в groupby.apply.
6. **`pd.from_dummies`**, `Series.case_when` (2.2+), `df.map`.
7. **Убраны десятки устаревших API** — см. таблицу выше.

Подготовка к pandas 3.0:

```python
pd.set_option("mode.copy_on_write", True)
pd.set_option("future.no_silent_downcasting", True)
import warnings
warnings.simplefilter("error", FutureWarning)   # ловить устаревания на CI
```

---

## 31. Шпаргалка

### Типовой пайплайн обработки

```python
import pandas as pd
import numpy as np

pd.set_option("mode.copy_on_write", True)

clean = (
    pd.read_csv("raw.csv", parse_dates=["date"], dtype_backend="pyarrow")
      .rename(columns=lambda c: c.strip().lower().replace(" ", "_"))
      .drop_duplicates()
      .dropna(subset=["id", "amount"])
      .astype({"category": "category"})
      .query("amount > 0 and date >= '2024-01-01'")
      .assign(
          month=lambda d: d.date.dt.to_period("M").astype(str),
          amount_log=lambda d: np.log1p(d.amount),
          is_big=lambda d: d.amount > d.amount.quantile(0.95),
      )
      .sort_values(["month", "amount"], ascending=[True, False])
      .reset_index(drop=True)
)

report = (
    clean.groupby(["month", "category"], observed=True, as_index=False)
         .agg(
             orders=("id", "count"),
             revenue=("amount", "sum"),
             avg_check=("amount", "mean"),
         )
         .assign(share=lambda d: d.revenue / d.groupby("month").revenue.transform("sum"))
)

report.to_parquet("report.parquet", index=False)
```

### Быстрый справочник операций

| Задача | Код |
|---|---|
| Первые строки | `df.head()` |
| Размер | `df.shape` |
| Типы и пропуски | `df.info()` |
| Статистика | `df.describe()` |
| Выбрать столбцы | `df[["a", "b"]]` |
| Фильтр | `df[df.a > 0]` / `df.query("a > 0")` |
| По метке | `df.loc[row, col]` |
| По позиции | `df.iloc[i, j]` |
| Новый столбец | `df["c"] = ...` / `df.assign(c=...)` |
| Удалить столбец | `df.drop(columns=["c"])` |
| Переименовать | `df.rename(columns={...})` |
| Сортировать | `df.sort_values("a")` |
| Пропуски | `df.isna().sum()` / `df.fillna(0)` / `df.dropna()` |
| Дубликаты | `df.drop_duplicates()` |
| Уникальные | `df.a.unique()` / `df.a.value_counts()` |
| Группировка | `df.groupby("k").agg(x=("v", "sum"))` |
| Оконное среднее по группе | `df.groupby("k").v.transform("mean")` |
| Сводная | `df.pivot_table(index=..., columns=..., values=..., aggfunc=...)` |
| Широкий → длинный | `df.melt(id_vars=...)` |
| JOIN | `df.merge(other, on="id", how="left")` |
| Вертикальная склейка | `pd.concat([a, b], ignore_index=True)` |
| Скользящее среднее | `df.v.rolling(7).mean()` |
| Сдвиг | `df.v.shift(1)` |
| Изменение | `df.v.pct_change()` |
| Тип | `df.astype({"a": "int32"})` |
| Ресемплинг | `ts.resample("ME").sum()` |
| Сохранить | `df.to_parquet("f.parquet")` |

### Полезные ссылки

* Официальная документация: <https://pandas.pydata.org/docs/>
* User Guide: <https://pandas.pydata.org/docs/user_guide/index.html>
* API Reference: <https://pandas.pydata.org/docs/reference/index.html>
* Cookbook (рецепты): <https://pandas.pydata.org/docs/user_guide/cookbook.html>
* Гайд по миграции на 2.0: <https://pandas.pydata.org/docs/whatsnew/v2.0.0.html>
