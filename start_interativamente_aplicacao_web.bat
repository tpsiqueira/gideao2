@echo off
chcp 65001
TITLE GIDEÃO - Aplicação Web
echo Inicializando aplicação web...
call conda activate D:\envs\gideao
call python "D:\gideao\gideao_project\manage.py" runserver 10.28.201.123:8989