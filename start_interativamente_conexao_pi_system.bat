@echo off
chcp 65001
TITLE GIDEÃO - Conexão com PI System
echo Inicializando script que realiza conexão com PI System...
call conda activate D:\envs\gideao
call python "D:\gideao\servidor_dados_pi.py"