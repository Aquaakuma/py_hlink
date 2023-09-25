from pathlib import Path
import pytest
import shutil
import subprocess
import random
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

    file_path = test_dir / 'test.jpg'
    file_size = random.randint(100, 100000)
    with open(file_path, "wb") as f:
        f.write(os.urandom(file_size))

    yield

def test_args_script(setup_test_environment):
    # 执行主脚本
    subprocess.run(["python", "main.py", "-source", "./1/2/3/", "-target", "./a/b/c/"])

    file_path = Path("./a/b/c/test.jpg")


    # 检查文件是否相同
    assert file_path.exists()