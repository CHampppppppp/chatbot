#!/usr/bin/env zsh

# 停止并移除容器，同时删除本地镜像
echo "执行: docker compose down --rmi local"
docker compose down --rmi local

# 检查前一个命令是否成功执行
if [ $? -ne 0 ]; then
    echo "docker compose down 执行失败，退出脚本"
    exit 1
fi

# 暂存本地更改并拉取远程代码
echo "执行: git stash && git pull -r"
git stash && git pull -r

# 检查前一个命令是否成功执行
if [ $? -ne 0 ]; then
    echo "git 操作执行失败，退出脚本"
    exit 1
fi

# 启动容器
echo "执行: docker compose up -d"
docker compose up -d

# 检查最后一个命令是否成功执行
if [ $? -ne 0 ]; then
    echo "docker compose up 执行失败"
    exit 1
fi

echo "所有命令执行完成"
