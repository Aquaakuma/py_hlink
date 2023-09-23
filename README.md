# Python媒体库硬连接脚本
这是一个用于管理媒体文件并在源目录和目标目录之间创建硬链接的 Python 脚本。它使用 SQLite 作为存储文件信息的数据库。

## 要求
- Python 3.x
- SQLite
## 安装
从 GitHub 克隆或下载该存储库。
使用以下命令安装所需的依赖项：pip install -r requirements.txt。
配置
在与脚本相同的目录中创建一个 config.ini 文件。
在 config.ini 文件中为每个要管理的源目录和目标目录对添加一个节。例如：
``````
[section1]
source_directory = /path/to/source_directory
target_directory = /path/to/target_directory
file_extensions = .mp4 .mkv .avi

[section2]
source_directory = /path/to/another_source_directory
target_directory = /path/to/another_target_directory
file_extensions = .jpg .png
``````
请确保将 /path/to/source_directory、/path/to/target_directory 和文件扩展名替换为实际的目录和文件扩展名。

使用方法
要使用脚本，请使用以下命令运行 main.py 文件：
``````
python main.py [-rebuild] [-source SOURCE] [-target TARGET]
-rebuild：重新构建目标目录中的数据。这将使用最新的文件信息更新数据库。
-source SOURCE：指定要从中创建硬链接的源目录。
-target TARGET：指定要创建硬链接的目标目录。
如果没有提供参数，脚本将使用 config.ini 文件中的配置为所有源目录和目标目录对创建硬链接。
``````
## 示例
在目标目录中重新构建数据：

``````
python main.py -rebuild
``````
从特定的源目录到特定的目标目录创建硬链接：

``````
python main.py -source /path/to/source_directory -target /path/to/target_directory
``````

## 许可证
本项目基于 MIT 许可证。
