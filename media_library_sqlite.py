import sqlite3
import logging
from texttable import Texttable


class MediaLibrarySQLite:
    def __init__(self, table_name, data):
        self.table_name = table_name
        self.data = data
        self.conn = sqlite3.connect('media_library.db')
        self.cursor = self.conn.cursor()
        self.create_table_if_not_exists()
        self.data_purge()

    def __del__(self):
        self.close_database()

    def close_database(self):
        logging.info("关闭数据库连接")
        self.cursor.close()
        self.conn.commit()
        self.conn.close()

    def create_table_if_not_exists(self):
        logging.debug(f"创建表格 {self.table_name}")
        query = f'''CREATE TABLE IF NOT EXISTS {self.table_name} (inode INTEGER PRIMARY KEY, file_path TEXT, target_path TEXT, file_type TEXT, last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'''
        self.cursor.execute(query)
        self.conn.commit()

    def which_item_not_exists(self):
        logging.info(f"查询 inode 是否存在于表格 {self.table_name} 中")
        inodes = [lst[0] for lst in self.data]
        placeholders = ', '.join(['?'] * len(inodes))
        query = f"SELECT inode FROM {self.table_name} WHERE inode IN ({placeholders})"
        self.cursor.execute(query, inodes)
        existing_inodes = set(row[0] for row in self.cursor.fetchall())
        items_exists = [lst for lst in self.data if lst[0] not in existing_inodes]
        return items_exists
    
    def data_purge(self):
        raw_data = self.data
        ripe_data = []
        replicate = False
        for item in raw_data:
            if len(item) != 4:
                raise ValueError("daata中的元素不是含有 4 个元素的列表")
            
            found_duplicate = False
            for index, ripe_item in enumerate(ripe_data):
                if ripe_item[0] == item[0]:
                    for i in range(len(ripe_item)-1):
                        if item[i+1] != ripe_data[index][i+1]:
                            ripe_data[index][i+1] = f"{item[i+1]}, {ripe_data[index][i+1]}"
                    found_duplicate = True
                    break
            if not found_duplicate:
                replicate = True
                ripe_data.append(item)
        if replicate:
            logging.debug("列表中存在重复的内容，已进行合并")
        self.data = ripe_data
        return
    
    def which_item_exists(self):
        logging.info(f"查询 inode 是否存在于表格 {self.table_name} 中")
        inodes = [lst[0] for lst in self.data]
        placeholders = ', '.join(['?'] * len(inodes))
        query = f"SELECT inode FROM {self.table_name} WHERE inode IN ({placeholders})"
        self.cursor.execute(query, inodes)
        rows = self.cursor.fetchall()
        existing_inodes = set(row[0] for row in rows)
        return existing_inodes

    def insert_data(self):
        logging.info(f"插入数据到表格 {self.table_name}")
        insert_values = []
        update_values = []
        existing_inodes = self.which_item_exists()

        for lst in self.data:
            if lst[0] in existing_inodes:
                update_values.append(lst)
            else:
                insert_values.append(lst)

        if insert_values:
            insert_query = f'INSERT INTO {self.table_name} (inode, file_path, target_path, file_type) VALUES (?, ?, ?, ?)'
            self.cursor.executemany(insert_query, insert_values)

        if update_values:
            update_query = f'UPDATE {self.table_name} SET file_path = ?, target_path = ?, file_type = ? WHERE inode = ?'
            self.cursor.executemany(update_query, update_values)

        self.conn.commit()

    def delete_data(self):
        logging.info(f"从表格 {self.table_name} 中删除数据")
        query = f'DELETE FROM {self.table_name} WHERE inode = ?'
        self.cursor.executemany(query, [(item[0],) for item in self.data])
        self.conn.commit()

    def rebuild_data(self):
        logging.info(f"清空表格 {self.table_name}")
        self.cursor.execute(f'DELETE FROM {self.table_name}')
        logging.info("重新写入数据")
        self.insert_data()
        self.conn.commit()
    
    def get_data(self):
        logging.info(f"获取 {self.table_name} 所有内容")
        query = f"SELECT * FROM {self.table_name}"
        self.cursor.execute(query)
        return self.cursor.fetchall()


    def print_pretty_table_from_db(self):
        logging.info(f"打印表格 {self.table_name}")
        rows = self.get_data()
        column_names = [description[0]
                        for description in self.cursor.description]

        table = Texttable()
        table.header(column_names)
        for row in rows:
            table.add_row(row)


        logging.info(f"\n{table.draw()}")
