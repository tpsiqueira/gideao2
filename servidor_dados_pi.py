# -*- coding: utf-8 -*-
import socketserver as SocketServer
import gideaoPI as gp
import pandas as pd


class MyTCPHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        def arrumaTemposValores(dfgp):
            tempos = ",".join(dfgp["timestamp"].tolist())
            valores = ",".join(dfgp["valor"].astype(str).tolist())
            saida = tempos[:-1] + "\n" + valores[:-1]
            return saida

        self.data = self.request.recv(1024).strip()
        argumentos = self.data.decode("utf-8").split(",")
        nome_servidor = argumentos[0]
        tag_corr = argumentos[1]

        if not nome_servidor or not tag_corr:
            return

        inicio_corr = argumentos[2]
        fim_corr = argumentos[3]
        estadosDiscretos = eval(argumentos[4])    

        conexao_corr = servidores[nome_servidor]

        dfgp = gp.getValoresArmazenados(
            conexao_corr,
            tag_corr,
            inicio_corr,
            fim_corr,
            estadosDiscretos,
        )

        if isinstance(dfgp, pd.DataFrame):
            self.request.sendall(str.encode(arrumaTemposValores(dfgp)))


if __name__ == "__main__":
    # ==================================================================================
    # Estabelece conexoes com servidores PI e AF
    # ==================================================================================

    try:
        global servidores
        servidores = {
            # UO-BC
            "SBCPI01": gp.getServidor("SBCPI01", "PI"),
            "SBCPI02": gp.getAFDataBase("UO-BC", gp.getServidor("SBCPIAF01", "AF")),
            # UO-BS
            "SBS00AS25": gp.getServidor("SBS00AS25", "PI"),
            "SBS00AS30": gp.getAFDataBase(
                "Elevação e Escoamento", gp.getServidor("SBS00AS30", "AF")
            ),
            # UO-ES
            "SESAUPI01": gp.getServidor("SESAUPI01", "PI"),
            "SESAUAF01": gp.getAFDataBase("UO-ES", gp.getServidor("SESAUAF01", "AF")),
            # Ambiente integrado
            "SEP00PIINT01": gp.getServidor("SEP00PIINT01", "PI"),
        }
    except Exception as e:
        raise Exception(
            "erro ao estabelecer conexoes com servidores PI e AF: {}".format(e)
        )

    HOST, PORT = "npaa9682.petrobras.biz", 6969
    print("Utilizando o servidor {} e a porta {} ...".format(HOST, PORT))
    server = SocketServer.TCPServer((HOST, PORT), MyTCPHandler)
    print("Conexoes com servidores PI e AF disponibilizadas")
    server.serve_forever()
