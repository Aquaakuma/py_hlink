from media_library_sqlite import MediaLibrarySQLite
from pathlib import Path
import configparser
import os
import argparse
import subprocess

def files_filter(mode='suffix', file_path=None, file_extensions=None):
    if mode == 'all':
        return True
    elif mode == 'suffix':
        if Path(file_path).suffix in file_extensions:
            return True
        else:
            return False
    else:
        return True

def create_date(source_directory=None, target_directory=None, file_extensions=None, filter_mode='suffix'):
    data_list = []

    if source_directory is None and target_directory:
        for file_path in Path(target_directory).glob('**/*'):
            if file_path.is_file() and files_filter('all'):
                data_list.append([os.stat(file_path).st_ino, None, str(file_path), file_path.suffix])
        return data_list

    for file_path in Path(source_directory).glob('**/*'):
        
        if file_path.is_file() and files_filter(filter_mode, file_path, file_extensions):
            source_file = file_path
            target_file = Path(target_directory / file_path.relative_to(source_directory))
            # 获取源文件的 inode 信息
            source_inode = os.stat(source_file).st_ino

            # 建立一个存储数据的列表
            data = [source_inode, str(source_file), str(target_file), file_path.suffix]
            data_list.append(data)
    
    return data_list

def rebuild_data(target_directory):
    table_name = Path(target_directory).name
    data_list = create_date(target_directory=target_directory, filter_mode='all')
    hlink_sql = MediaLibrarySQLite(table_name, data_list)
    hlink_sql.rebuild_data()
    hlink_sql.print_pretty_table_from_db()

def create_hardlink(source_file, target_file):
    system = os.name
    if system == 'nt':
        Path(target_file).hardlink_to(source_file)
        return
    elif system == 'posix':
        unix = os.uname().sysname
        if unix == 'Linux':
            Path(target_file).hardlink_to(source_file)
            return
        elif unix in ['FreeBSD', 'Darwin']:
            try:
                subprocess.run(['cp', '-l', source_file, target_file], check=True)
            except subprocess.CalledProcessError as e:
                print(f'创建硬链接失败：{str(e)}')
                raise
            return
    else:
        print("未知系统")
        return

def files_hlinker(source_directory, target_directory, file_extensions):
    table_name = Path(target_directory).name
    data_list = create_date(source_directory, target_directory, file_extensions)

    # 创建 MediaLibrarySQLite 对象并执行链接媒体文件的操作
    hlink_sql = MediaLibrarySQLite(table_name, data_list)
    hlink_list = hlink_sql.which_item_not_exists()
    insert_list = []

    for item in hlink_list:
        try:
            Path(item[2]).parent.mkdir(parents=True, exist_ok=True)
            create_hardlink(item[1], item[2])
            print(f'已从 {item[1]} 创建了硬链接到 {item[2]}')
            insert_list.append(item)
        except OSError as e:
            print(f'创建硬链接失败：{str(e)}')
            if e.winerror == 183:
                print(f'链接已存在，将记录写入数据库中')
                insert_list.append(item)

    if not insert_list:
        print("没有文件被硬链接")
    else:
        hlink_sql.data = insert_list
        hlink_sql.insert_data()

    hlink_sql.print_pretty_table_from_db()
    # hlink_sql.close_database()


def load_config(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    return config

def is_subdirectory(child_directory, parent_directory):
    parent_directory = Path(parent_directory)
    child_directory = Path(child_directory)

    is_subdirectory = child_directory.is_relative_to(parent_directory)

    return is_subdirectory



def porcess_hlink(source=None, target=None, rebuild=False):
    config_file = 'config.ini'
    config = load_config(config_file)
    if rebuild is True:
        for section_name in config.sections():
            target_directory = config.get(section_name, 'target_directory')
            rebuild_data(target_directory)
        return
        
    elif source is None and target is None:
        for section_name in config.sections():
            source_directory = config.get(section_name, 'source_directory')
            target_directory = config.get(section_name, 'target_directory') 
            file_extensions = config.get(section_name, 'file_extensions').split()

            files_hlinker(source_directory, target_directory, file_extensions)        
        return

    elif Path(source).is_dir() and Path(target).is_dir():
        for section_name in config.sections():
            target_directory = config.get(section_name, 'target_directory') 
            file_extensions = config.get(section_name, 'file_extensions').split()
            if is_subdirectory(Path(target), target_directory):
                files_hlinker(source, target, file_extensions)
                return
        print(f"目标路径不属于任何目标目录")
        return


            
    else:
        print("没有进行任何操作")
    

def main():
    parser = argparse.ArgumentParser(description='脚本描述')
    parser.add_argument('-rebuild', action='store_true', help='重新构建数据')
    parser.add_argument('-source', type=str, help='源文件')
    parser.add_argument('-target', type=str, help='目标文件')
    args = parser.parse_args()

    if args.rebuild:
        porcess_hlink(rebuild=args.rebuild)

    elif args.source and args.target:
        source_file = args.source
        target_file = args.target

        porcess_hlink(source_file, target_file)

    else:
        # 没有提供参数时，默认执行原来的操作
        # 遍历所有分节并执行链接媒体文件的操作
        porcess_hlink()



if __name__ == '__main__':
    main()