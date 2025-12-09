from sqlite3 import connect, Row
database = 'db/campus_data.db'


def getProcess(sql, vals) -> list:
    conn = connect(database)
    conn.row_factory = Row
    cursor = conn.cursor()
    cursor.execute(sql, vals)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data


def postProcess(sql, vals) -> bool:
    affected_rows = 0
    try:
        conn = connect(database)
        cursor = conn.cursor()
        cursor.execute(sql, vals)
        conn.commit()
        affected_rows = cursor.rowcount
    except Exception as e:
        print(f"Error : {e}")
    finally:
        cursor.close()
        conn.close()
    return True if affected_rows > 0 else False


def createAdminTable():
    """Create admin table if it doesn't exist"""
    try:
        conn = connect(database)
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        conn.commit()
        cursor.close()
        conn.close()
        print("Admin table ready!")
        return True
    except Exception as e:
        print(f"Error creating admin table: {e}")
        return False


def getAll(table) -> list:
    sql = f"SELECT * FROM {table}"
    return getProcess(sql, [])


def getRecord(table, **kwargs) -> list:
    keys = list(kwargs.keys())
    vals = list(kwargs.values())
    flds = []
    for key in keys:
        flds.append(f"{key} =?")
    fields = " AND ".join(flds)
    sql = f"SELECT * FROM {table} WHERE {fields}"
    return getProcess(sql, vals)


def addRecord(table, **kwargs) -> bool:
    keys = list(kwargs.keys())
    vals = list(kwargs.values())
    flds = ['?'] * len(keys)
    fldstring = "(" + ",".join(flds) + ")"
    fields = ",".join(keys)
    sql = f"INSERT INTO {table} ({fields}) VALUES {fldstring}"
    return postProcess(sql, vals)


def deleteRecord(table, **kwargs) -> bool:
    keys = list(kwargs.keys())
    vals = list(kwargs.values())
    flds = []
    for key in keys:
        flds.append(f"{key} =?")
    fields = " AND ".join(flds)
    sql = f"DELETE FROM {table} WHERE {fields}"
    return postProcess(sql, vals)


def updateRecord(table, **kwargs) -> bool:
    keys = list(kwargs.keys())
    vals = list(kwargs.values())
    newvals = []
    flds = []
    for index in range(1, len(keys)):
        flds.append(f"{keys[index]} =?")
        newvals.append(vals[index])
    fields = ",".join(flds)
    sql = f"UPDATE {table} SET {fields} WHERE {keys[0]} =?"
    return postProcess(sql, newvals + [vals[0]])
