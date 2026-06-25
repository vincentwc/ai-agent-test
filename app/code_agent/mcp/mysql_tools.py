import os
import sys
from typing import Optional, Dict, Any, Annotated, List

import pymysql
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from sqlalchemy.dialects.mssql.information_schema import columns

mcp = FastMCP()


class Response(BaseModel):
    success: bool
    database: str
    table: str
    data: Optional[dict] | Optional[list]
    rowcount: Optional[int] | None


MYSQL_CONFIG = {
    "host": "192.168.64.3",
    "port": 3306,
    "user": "root",
    "password": "root",
    "charset": "utf8mb4",
    "connect_timeout": 10,
}


def get_connection(db):
    for var in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'no_proxy', 'NO_PROXY']:
        os.environ.pop(var, None)

    config = MYSQL_CONFIG.copy()
    if db:
        config['database'] = db

    try:
        connection = pymysql.connect(**config)
        return connection
    except Exception as e:
        msg = f'mysql connection error: {str(e)}'
        return msg


def execute_query(command, database=None, params=None, commit=False):
    connection = get_connection(database)
    print(connection)
    if not isinstance(connection, pymysql.Connection):
        return connection
    else:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(command, params)
            result = cursor.fetchall()

            if commit:
                connection.commit()
            return result, cursor.rowcount


@mcp.tool(name="mysql_list_databases", description="列举出MySQL中包含哪些数据库")
def mysql_list_databases():
    try:
        result = execute_query("show databases")
        if not isinstance(result, list):
            return result
        databases = [row["Database"] for row in result]
        return Response(
            success=True,
            database='',
            table='',
            data=databases
        )
    except Exception as e:
        msg = f"mysql list databases error: {str(e)}"
        return msg


@mcp.tool(name="mysql_list_tables", description="获取指定数据库中的所有表")
def mysql_list_tables(database: str):
    try:
        result = execute_query("show tables", database=database)
        tables = [list(row.values())[0] for row in result]
        return Response(
            success=True,
            database=database,
            table='',
            data=tables
        )
    except Exception as e:
        msg = f"mysql list tables error: {str(e)}"
        return msg


@mcp.tool(name="mysql_describe_tables", description="获取表结构信息")
def mysql_describe_tables(database: str, table: str):
    try:
        return execute_query(f"describe {table}", database=database)
    except Exception as e:
        msg = f"mysql describe table error: {str(e)}"
        return msg


@mcp.tool(name="mysql_execute_query", description="执行SQL查询语句")
def mysql_execute_query(command, database=None, params: Optional[list] = None):
    try:
        params_tuple = tuple(params) if params else None
        result = execute_query(command, database=database, params=params_tuple, commit=True)
        return Response(
            success=True,
            database=database,
            table='',
            data=result
        )
    except Exception as e:
        msg = f"query table error: {str(e)}"
        return msg


@mcp.tool(name="mysql_insert_date", description="插入数据到指定表")
def mysql_insert_date(database: str, table: str, data: Dict[str, Any]):
    columns = list(data.keys())
    values = list(data.values())
    print(columns)
    print(values)
    placeholders = ','.join(['%s'] * len(values))
    command = f"insert into {table} ({','.join(columns)}) values ({placeholders})"
    print(command)
    try:
        result, rowcount = execute_query(command, database=database, params=values, commit=True)
        return Response(
            success=True,
            database=database,
            table=table,
            data=result,
            rowcount=rowcount,
        )
    except Exception as e:
        msg = f"mysql insert date error: {str(e)}"
        return msg


@mcp.tool(name="mysql_update_data", description="更新指定表中的数据")
def mysql_update_data(database: str, table: str, data: Dict[str, Any], where: Dict[str, Any]):
    set_clause = ','.join([f"{col} = %s" for col in data.keys()])
    where_clause = 'and'.join([f"{col} = %s" for col in where.keys()])

    command = f"update {table} set {set_clause} where {where_clause}"

    set_params = list(data.values())
    where_params = list(where.values())

    params = set_params + where_params

    print(command)
    try:
        result, rowcount = execute_query(command, database=database, params=tuple(params), commit=True)
        return Response(
            success=True,
            database=database,
            table=table,
            data=result,
            rowcount=rowcount,
        )
    except Exception as e:
        msg = f"mysql update data error: {str(e)}"
        return msg


@mcp.tool(name="mysql_delete_data", description="删除指定表中的数据")
def mysql_delete_data(database: str, table: str, where: Dict[str, Any]):
    where_clause = 'and'.join([f"{col} = %s" for col in where.keys()])

    command = f"delete from {table} where {where_clause}"

    params = list(where.values())

    print(command)
    try:
        result, rowcount = execute_query(command, database=database, params=tuple(params), commit=True)
        return Response(
            success=True,
            database=database,
            table=table,
            data=result,
            rowcount=rowcount,
        )
    except Exception as e:
        msg = f"mysql update data error: {str(e)}"
        return msg


@mcp.tool(name="mysql_create_database", description="创建指定数据库")
def mysql_create_database(database: str, charset: str = "utf8mb4"):
    command = f"create database {database} character set {charset}"
    print(command)
    try:
        result = execute_query(command)
        return Response(
            success=True,
            database=database,
            table='',
            data=result,
        )
    except Exception as e:
        msg = f"mysql create database error: {str(e)}"
        return msg


@mcp.tool(name="mysql_create_table", description="创建指定表")
def mysql_create_table(
        database: str,
        table_name: str,
        table_columns: Annotated[List[str], Field(description="表列定义，每个列用逗号分隔",
                                                  examples="`id` not null auto_increment primary key,`name` varchar(255) not null,`age` int not null")],
        table_schema: Annotated[List[str], Field(description="表结构补充信息",
                                                 examples="engine=InnoDB default charset=utf8mb4 collation=utf8mb4_general_ci"),]):
    command = f"create table {table_name} ({table_columns}) {table_schema}"
    print(command)
    try:
        result, rowcount = execute_query(command, database=database)
        return Response(
            success=True,
            database=database,
            table=table_name,
            data=result,
            rowcount=rowcount,
        )
    except Exception as e:
        msg = f"mysql create table error: {str(e)}"
        return msg


@mcp.tool(name="mysql_execute_command", description="执行指定数据库命令,如变更表结构、增减字段等")
def mysql_execute_command(database: str, command: str):
    try:
        result, rowcount = execute_query(command, database=database, commit=True)

        return Response(
            success=True,
            database=database,
            table='',
            data=result,
            rowcount=rowcount,
        )
    except Exception as e:
        msg = f"mysql execute command error: {str(e)}"
        return msg


if __name__ == '__main__':
    mysql_create_database("test3")
