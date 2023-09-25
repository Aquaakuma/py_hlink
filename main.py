import argparse
from configparser import ConfigParser
from pathlib import Path
import os
from media_library_sqlite import MediaLibrarySQLite
import subprocess
import logging


# 配置日志格式器
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', '%Y-%m-%d %H:%M:%S')

# 配置日志处理器
handler = logging.StreamHandler()
handler.setFormatter(formatter)

# 获取根日志记录器并添加处理器
logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

class MediaLibraryBuilder:
    def __init__(self, target_dir='', extensions=[]):
        # 初始化属性
        if not target_dir and not extensions:
            raise ValueError("请输入正确的参数！")
        self.target_dir = target_dir
        self.extensions = extensions
    

    def is_target(self, file_path=''):
        if Path(file_path).suffix in self.extensions:
            return True
        else:
            return False
        
    def create_data(self):
        data_list = []
        if self.target_dir:
            for file_path in Path(self.target_dir).glob('**/*'):
                if file_path.is_file() and self.is_target(str(file_path)):
                    data_list.append([os.stat(file_path).st_ino, None, str(file_path), file_path.suffix])
        return data_list

    def rebuild_data(self):
        table_name = Path(self.target_dir).name
        data_list = self.create_data()
        hlink_sql = MediaLibrarySQLite(table_name, data_list)
        hlink_sql.rebuild_data()
        hlink_sql.print_pretty_table_from_db()
    


    
class MediaLibraryLinker(MediaLibraryBuilder):
    def __init__(self, source_dir, target_dir='', extensions=[]):
        super().__init__(target_dir, extensions)
        self.source_dir = source_dir
    

    
    @staticmethod
    def create_hardlink(source_file, target_file):
        system = os.name
        if system == 'nt':
            Path(target_file).hardlink_to(source_file)
            return
        elif system == 'posix':
            unix = os.uname().sysname # type: ignore
            if unix == 'Linux':
                Path(target_file).hardlink_to(source_file)
                return
            elif unix in ['FreeBSD', 'Darwin']:
                try:
                    subprocess.run(['cp', '-l', source_file, target_file], check=True)
                except subprocess.CalledProcessError as e:
                    logging.info(f'创建硬链接失败：{str(e)}')
                    raise
                return
        else:
            logging.info("未知系统")
            return

    
    def create_data(self):
        data_list = []
        for file_path in Path(self.source_dir).glob('**/*'):
            
            if file_path.is_file() and self.is_target(str(file_path)):
                source_file = file_path
                target_file = Path(self.target_dir / file_path.relative_to(self.source_dir))
                # 获取源文件的 inode 信息
                source_inode = os.stat(source_file).st_ino

                # 建立一个存储数据的列表
                data = [source_inode, str(source_file), str(target_file), file_path.suffix]
                data_list.append(data)
        
        return data_list
    

    def files_hlinker(self, table_name=''):
        if table_name == '':
            table_name = Path(self.target_dir).name
        data_list = self.create_data()

        # 创建 MediaLibrarySQLite 对象并执行链接媒体文件的操作
        hlink_sql = MediaLibrarySQLite(table_name, data_list)
        hlinked_list = hlink_sql.which_item_exists()
        hlink_list = [lst for lst in data_list if lst[0] not in hlinked_list]

        insert_list = []

        for item in hlink_list:
            try:
                Path(item[2]).parent.mkdir(parents=True, exist_ok=True)
                self.create_hardlink(item[1], item[2])
                logging.info(f'已从 {item[1]} 创建了硬链接到 {item[2]}')
                insert_list.append(item)
            except OSError as e:
                logging.info(f'创建硬链接失败：{str(e)}')
                if e.winerror == 183:
                    logging.info(f'链接已存在，将记录写入数据库中')
                    insert_list.append(item)

        if not insert_list:
            logging.info("没有文件被硬链接")
        else:
            hlink_sql.data = insert_list
            hlink_sql.insert_data()
        hlink_sql.print_pretty_table_from_db()


    def build_cache(self):
        table_name = Path(self.target_dir).name
        data_list = self.create_data()
        data_list  += super().create_data()
        hlink_sql = MediaLibrarySQLite(table_name, data_list)
        hlink_sql.rebuild_data()
        hlink_sql.print_pretty_table_from_db()


def is_subdirectory(child_directory, parent_directory):
    parent_directory = Path(parent_directory)
    child_directory = Path(child_directory)

    is_subdirectory = child_directory.is_relative_to(parent_directory)

    return is_subdirectory

def load_config(config_file):
    config = ConfigParser()
    config.read(config_file)
    return config

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='脚本描述')
    parser.add_argument('-rebuild', action='store_true', help='重新构建数据')
    parser.add_argument('-build_cache', action='store_true', help='重新构建缓存')
    parser.add_argument('-source', type=str, help='源文件')
    parser.add_argument('-target', type=str, help='目标文件')
    args = parser.parse_args()

    config_file = 'config.ini'
    config = load_config(config_file)

    if args.rebuild:
        for section_name in config.sections():
            target_directory = config.get(section_name, 'target_directory')
            file_extensions = config.get(section_name, 'file_extensions').split()
            db = MediaLibraryBuilder(target_dir=target_directory, extensions=file_extensions)
            db.rebuild_data()

    elif args.build_cache:
        for section_name in config.sections():
            source_directory = config.get(section_name, 'source_directory')
            target_directory = config.get(section_name, 'target_directory') 
            file_extensions = config.get(section_name, 'file_extensions').split()
            db = MediaLibraryLinker(source_dir=source_directory, target_dir=target_directory, extensions=file_extensions)
            db.build_cache() 

    elif args.source and args.target:
        for section_name in config.sections():
            target_directory = config.get(section_name, 'target_directory') 
            file_extensions = config.get(section_name, 'file_extensions').split()
            if is_subdirectory(Path(args.target), target_directory):
                db = MediaLibraryLinker(source_dir=args.source, target_dir=args.target, extensions=file_extensions)
                db.files_hlinker(table_name=Path(target_directory).name)
                break

    else:
        # 没有提供参数时，默认执行原来的操作
        # 遍历所有分节并执行链接媒体文件的操作
        for section_name in config.sections():
            source_directory = config.get(section_name, 'source_directory')
            target_directory = config.get(section_name, 'target_directory') 
            file_extensions = config.get(section_name, 'file_extensions').split()
            db = MediaLibraryLinker(source_dir=source_directory, target_dir=target_directory, extensions=file_extensions)
            db.files_hlinker()        
        