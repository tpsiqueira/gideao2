@echo off
chcp 65001
TITLE GIDEÃO - Exportação de Instâncias
echo Inicializando script que realiza exportação de instâncias...
call conda activate D:\envs\gideao
call python "D:\gideao\exportador.py"