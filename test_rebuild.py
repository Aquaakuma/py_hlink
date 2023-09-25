from configparser import ConfigParser
from pathlib import Path
import pytest
import shutil
import random
import string
import os
from media_library_sqlite import MediaLibrarySQLite
from main import MediaLibraryBuilder


@pytest.fixture(scope="function")
def setup_test_environment():
    # 删除数据库文件
    db_file = Path("media_library.db")
    if db_file.exists():
        db_file.unlink()
    shutil.rmtree(str(Path('./a/b/c')), ignore_errors=True)
    Path("./a/b/c").mkdir(parents=True, exist_ok=True)

    # 创建测试所需的文件和目录
    test_dir = Path("./a/b/c")
    shutil.rmtree(str(test_dir), ignore_errors=True)
    test_dir.mkdir(parents=True, exist_ok=True)

    # 创建随机文件
    file_extensions = [".mp4", ".jpg", ".txt"]
    for _ in range(30):
        file_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        file_extension = random.choice(file_extensions)
        file_path = test_dir / (file_name + file_extension)
        file_size = random.randint(100, 100000)
        with open(file_path, "wb") as f:
            f.write(os.urandom(file_size))

    yield




def re_generate_directory():
    test_dir = Path("./a/b/c")
    shutil.rmtree(Path('./a/b/c'), ignore_errors=True)
    Path("./a/b/c").mkdir(parents=True, exist_ok=True)
    file_extensions = [".mp4", ".jpg", ".txt"]
    for _ in range(30):
        file_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        file_extension = random.choice(file_extensions)
        file_path = test_dir / (file_name + file_extension)
        file_size = random.randint(100, 100000)
        with open(file_path, "wb") as f:
            f.write(os.urandom(file_size))

def load_config(config_file):
    config = ConfigParser()
    config.read(config_file)
    return config



def test_rebuild_function(setup_test_environment, monkeypatch):
    # 模拟内部函数的行为
    def mock_rebuild_data(self):
        table_name = Path(self.target_dir).name
        data_list = self.create_data()
        hlink_sql = MediaLibrarySQLite(table_name, data_list)
        hlink_sql.rebuild_data()
        
        return set(row[0] for row in hlink_sql.get_data())


    # 使用monkeypatch替换内部函数
    monkeypatch.setattr(MediaLibraryBuilder, "rebuild_data", mock_rebuild_data)

    # 调用外部函数

    config_file = 'config.ini'
    config = load_config(config_file)

    before = []

    for section_name in config.sections():
        target_directory = config.get(section_name, 'target_directory')
        file_extensions = config.get(section_name, 'file_extensions').split()
        db = MediaLibraryBuilder(target_dir=target_directory, extensions=file_extensions)
        before.append(db.rebuild_data())

    re_generate_directory()
    after = []

    for section_name in config.sections():
        target_directory = config.get(section_name, 'target_directory')
        file_extensions = config.get(section_name, 'file_extensions').split()
        db = MediaLibraryBuilder(target_dir=target_directory, extensions=file_extensions)
        after.append(db.rebuild_data())


    # 验证结果是否符合预期
    assert not before == after



