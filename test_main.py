from pathlib import Path
import pytest
import shutil
import subprocess
import filecmp
import random
import string
import os

@pytest.fixture(scope="function")
def setup_test_environment():
    # 删除数据库文件
    db_file = Path("media_library.db")
    if db_file.exists():
        db_file.unlink()
    shutil.rmtree(str(Path('./a/b/c')), ignore_errors=True)
    Path("./a/b/c").mkdir(parents=True, exist_ok=True)

    # 创建测试所需的文件和目录
    test_dir = Path("./1/2/3")
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

def test_main_script(setup_test_environment):
    # 执行主脚本
    subprocess.run(["python", "main.py"])

    # 比较文件
    source_dir = Path("./1/2/3")
    target_dir = Path("./a/b/c")
    diff_files = filecmp.dircmp(source_dir, target_dir)
    diff_files.report_full_closure()

    # 获取排除的文件列表
    excluded_files = [f for f in diff_files.left_only if Path(f).suffix == ".txt"]

    # 检查文件是否相同
    assert diff_files.left_only == excluded_files