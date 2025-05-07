import os
from pathlib import Path
from setuptools import setup, find_packages

this_directory = os.path.abspath(os.path.dirname(__file__))
long_description = None

def list_files(top_directory:Path,current_directory:Path) -> list:
    rslt=[]
    a=(str(current_directory.relative_to(top_directory.parent)),[])
    for _file in current_directory.rglob('*'):
        if _file.is_dir():
            rslt.extend(list_files(top_directory,_file))
        if _file.is_file():
            a[1].append(str(_file.relative_to(top_directory.parent)))
    if len(a[1])!=0:
        rslt.append(a)
    return rslt
 
setup(
      name='beagle_runtime_api', # 包名称
      packages=find_packages(exclude=['__pycache__']), # 需要处理的包目录
      version='0.1.250415', # 版本
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Programming Language :: Python', 'Intended Audience :: Developers',
          'Programming Language :: Python :: 3.10',
      ],
      install_requires=['numpy'],
      # package_data={'': ['*.json']},
      author='H. Xu', # 作者
      description='Yet another tools for darwin3.', # 介绍
      scripts=["script/uninstall_darwinos_node.sh"],
      data_files=list_files(Path("beagle_driver"), Path("beagle_driver")),
      # scripts=["script/restart_dma.sh", "script/init.sh"], 
      # long_description=long_description, # 长介绍，在pypi项目页显示
      # long_description_content_type='text/markdown', # 长介绍使用的类型
      license='GPL', # 协议
      python_requires='>=3.8'
    )