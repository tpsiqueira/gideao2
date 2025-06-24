"""
Este script fornece a funcionalidade de exportacao de instancias cadastradas (e 
possivelmente rotuladas) no GIDEAO. 

As seguintes premissas sao assumidas por este script:
    * A indicacao de quais instancias devem ser exportadas por este script eh feita por 
    meio do atributo status_exportacao, que pode assumir apenas os seguintes valores:
        * Pendente (a instancia estah pendente de ser exportada);
        * Exportando (a instancia estah sendo exportada);
        * Exportada (a instancia foi exportada ao menos uma vez e a ultima exportacao 
        foi bem sucedida);        
        * Erro (a ultima exportacao da instancia foi mal sucedida).
    * Todas as grandezas industriais consideradas relevantes para o 3W dataset, e 
    exclusivamente essas, sao consideradas na exportacao realizada por este script. 
    Quando qualquer uma dessas grandezas industriais nao estiver corretamente 
    configurada no banco de dado do GIDEAO, a exportacao de dados referente a ela nao 
    eh feita e a coluna referente a ela no arquivo PARQUET fica complementamente vazia;
    * Todas as variaveis industriais tem, necessariamente, suas unidades de medidas 
    padronizadas para aquelas consideradas no 3W dataset conforme configuradas no 
    GIDEAO;
    * Nao hah qualquer gap de rotulagem entre amostras de uma mesma instancia qualquer. 
    Cabe ressaltar que existe script especifico (chamado elimine_gaps_rotulagem.py) para 
    exportacao e eliminacao desse tipo de gap. Alem disso, atualmente o proprio GIDEAO 
    impede criacao de instancia com qualquer gap de rotulagem;
    * O periodo exportado em cada instancia se inicia no inicio da primeira amostra e se 
    finaliza no final da ultima amostra. Portanto, o perido exportado nao coincide
    necessariamente com o periodo da analise, que geralmente eh mais amplo;
    * Amostra completamente nao rotulada eh adicionada por este script no inicio da 
    analise em funcao da configuracao do seu tipo de grandeza especialista. Essa adicao
    eh exclusivamente para a exportacao. A amostra adicionada nao eh persisitida (salva)
    no banco de dados;
    * Colunas com rotulos de observacoes e estados de poco sao adicionadas nas 
    exportacoes de instancias associadas apenas a grandezas especialistas diferentes de 
    "Exploration". O racional eh que esse tipo de grandeza especialista naturalmente nao
    demanda e/ou tem rotulagem e estados conhecidos;
    * Para instancias associadas a grandeza especialista "Exploration", a exportacao eh 
    feita com interpolacao a cada 1 minuto. Caso contrario, a interpolacao eh feita a 
    cada 1 segundo;
    * Para instancia sem qualquer amostra, este script nao gera arquivo PARQUET de 
    saida;
    * Aceita-se exportacoes de variaveis industriais de uma mesma instancia a partir de 
    diferentes servidores. Afinal o banco de dados do GIDEAO controla informacoes sobre
    servidor no nivel de variavel industrial.

A execucao deste script nao resulta em perda significativa de informacoes no banco de 
dados do GIDEAO. O unico atribuito que pode ser alterado durante execucao deste script 
eh o status_exportacao, que nao armazena informacao considerada sensivel.

Este script nao utiliza parametros em linha de comando.

Resultados:

    1) Um arquivo PARQUET para cada instancia nao vazia com a formatacao do 3W dataset;
    2) Arquivo .log com mensagens de informacoes, alertas e erros. Quando da execucao
    deste script, se esse arquivo jah existir ele eh incrementado com mensagens geradas.

Exemplos de uso:

    >python exportador.py

Autor: Ricardo Vargas (UR8D).

Ultima atualizacao: julho de 2024.
"""

# ======================================================================================
# BIBLIOTECAS ADICIONAIS
# ======================================================================================

import sys
import django
import os
import pandas as pd
import numpy as np
import logging
import win32com.client
import datetime
import time
from pathlib import Path

# ======================================================================================
# CONSTANTES
# ======================================================================================

# Endereco onde se encontra o db.sqlite3
PATH_GIDEAO = r"D:\gideao\gideao_project"

# Endereco onde se encontra o gideaoPI.py
PATH_GIDEAO_PI = r"D:\gideao"

# Endereco base para exportacao de instancias
PATH_EXPORTACAO = r"D:\resultado_exportador_gideao"

# Frequencias de interpolacao que podem ser utilizadas durante exportacao
SPAN_DEFAULT = "1s"  # Default do 3W dataset
SPAN_EXPLORATION = "1m"  # Especial para exploracao

# Frequencias de geracao de timestamps pelo metodo date_range
# OBS 1: optou-se em gerar os timestamps, e nao utilizar do retorno do gideaoPI.py
# OBS 2: essas constantes sao diferentes porque seus possiveis valores sao diferentes
FREQ_DEFAULT = "1s"  # Default do 3W dataset
FREQ_EXPLORATION = "1t"  # Especial para exploracao

# Nome do arquivo no qual sao persistidos logs de informacoes, alertas e erros
PREFIXO_ARQUIVO_LOG = "exportador_"

# Tipos das grandezas industriais utilizadas. True/False se refere a ser do tipo ESTADO
# ou nao. Essa distincao se faz necessaria principalmente devido as formas com as quais
# unidades de medida sao convertidas. Para mais detalhes, ver explicacao na funcao 
# converta_unidade_medida
TIPOS_GRANDEZAS_INDUSTRIAIS = {
    "ABER-CKGL": False,
    "ABER-CKP": False,
    "ESTADO-DHSV": True,
    "ESTADO-M1": True,
    "ESTADO-M2": True,
    "ESTADO-PXO": True,
    "ESTADO-SDV-GL": True,
    "ESTADO-SDV-P": True,
    "ESTADO-W1": True,
    "ESTADO-W2": True,
    "ESTADO-XO": True,
    "P-ANULAR": False,
    "P-JUS-BS": False,
    "P-JUS-CKGL": False,
    "P-JUS-CKP": False,
    "P-MON-CKGL": False,
    "P-MON-CKP": False,
    "P-MON-SDV-P": False,
    "P-PDG": False,
    "PT-P": False,
    "P-TPT": False,
    "QBS": False,
    "QGL": False,
    "T-JUS-CKP": False,
    "T-MON-CKP": False,
    "T-PDG": False,
    "T-TPT": False,
}

# Nomes das grandezas industriais utilizadas
GRANDEZAS_INDUSTRIAIS = list(TIPOS_GRANDEZAS_INDUSTRIAIS.keys())

# Estados de poco considerados atualmente no 3W dataset e seus codigos
ESTADOS_POCO = {
    "OPEN": 0,
    "SHUT-IN": 1,
    "FLUSHING DIESEL": 2,
    "FLUSHING GAS": 3,
    "BULLHEADING": 4,
    "CLOSED WITH DIESEL": 5,
    "CLOSED WITH GAS": 6,
    "RESTART": 7,
    "DEPRESSURIZATION": 8,
    "UNKNOWN": np.nan,
}

# Tipo para os vetores com grandezas industriais. Para instancias persistidas em 
# arquivos PARQUET, escolheu-se utilizar apenas float
GRANDEZAS_INDUSTRIAIS_DTYPE = dict(
    zip(GRANDEZAS_INDUSTRIAIS, [float] * len(GRANDEZAS_INDUSTRIAIS))
)

# Tipo para os vetores com class e state. Para instancias persistidas em 
# arquivos PARQUET, escolheu-se utilizar apenas "Int16", tipo do Numpy que aceita nulos
CLASS_STATE_DTYPES = {"class": "Int16", "state": "Int16"}

# Configuracoes usadas em geracao de arquivos PARQUET
PARQUET_EXTENSION = ".parquet"
PARQUET_ENGINE = "pyarrow"
PARQUET_COMPRESSION = "brotli"
PARQUET_DTYPES = GRANDEZAS_INDUSTRIAIS_DTYPE | CLASS_STATE_DTYPES

# Tipos para amostras_df
AMOSTRAS_DTYPES = CLASS_STATE_DTYPES | {
    "inicio": "datetime64[ns]",
    "fim": "datetime64[ns]",
}

# ======================================================================================
# CONFIGURA logging
# ======================================================================================

logging.basicConfig(
    filename=PREFIXO_ARQUIVO_LOG
    + datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    + ".log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logging.info("iniciando configuracao do script exportador...")
logging.info("principais constantes definidas:")
logging.info("\tendereco onde se encontra o db.sqlite3: {}".format(PATH_GIDEAO))
logging.info("\tendereco onde se encontra o gideaoPI.py: {}".format(PATH_GIDEAO_PI))
logging.info(
    "\tendereco base para exportacao de instancias: {}".format(PATH_EXPORTACAO)
)
logging.info("\tfrequencia de interpolacao default: {}".format(SPAN_DEFAULT))
logging.info(
    "\tfrequencia de interpolacao para exploracao: {}".format(SPAN_EXPLORATION)
)
logging.info(
    "\t# grandezas industriais utilizadas: {} {}".format(
        len(GRANDEZAS_INDUSTRIAIS), GRANDEZAS_INDUSTRIAIS
    )
)

# ======================================================================================
# CONFIGURA E IMPORTA MODULOS DO GIDEAO (PROJETO DJANGO)
# ======================================================================================

if not Path(PATH_GIDEAO).exists():
    logging.critical("endereco onde o db.sqlite3 deveria ser encontrado nao existe")
    raise (Exception("endereco associado a {} eh invalido".format(PATH_GIDEAO)))
sys.path.append(PATH_GIDEAO)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gideao_project.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
try:
    django.setup()
    from admin_app.models import (
        grandeza_especialista,
        grandeza_industrial,
        variavel_industrial,
        unidade_medida,
    )
    from monitor_app.models import analise, amostra
except Exception as e:
    logging.critical("erro ao configurar ou importar o projeto django")
    raise Exception("erro ao configurar ou importar o projeto django: {}".format(e))

# ======================================================================================
# IMPORTA O gideaoPI
# ======================================================================================

if not Path(PATH_GIDEAO_PI).exists():
    logging.critical("endereco onde o gideaoPI.py deveria ser encontrado nao existe")
    raise (Exception("endereco associado a {} eh invalido".format(PATH_GIDEAO_PI)))
sys.path.append(PATH_GIDEAO_PI)
try:
    import gideaoPI as gp
except Exception as e:
    logging.critical("erro ao importar o gideaoPI")
    raise Exception("erro ao importar o gideaoPI: {}".format(e))

# ======================================================================================
# CONFIGURA DIRETORIO BASE PARA EXPORTACAO DE INSTANCIAS
# ======================================================================================

if not Path(PATH_EXPORTACAO).exists():
    logging.critical("endereco base para exportacao de instancias nao existe")
    raise (Exception("endereco associado a {} eh invalido".format(PATH_EXPORTACAO)))
else:
    global dir_base_exportacao
    dir_base_exportacao = Path(PATH_EXPORTACAO)

# ======================================================================================
# Estabelece conexoes com servidores PI e AF
# ======================================================================================

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
    logging.critical("erro ao estabelecer conexoes com servidores PI e AF")
    raise Exception("erro ao estabelecer conexoes com servidores PI e AF: {}".format(e))

# ======================================================================================
# FUNCOES
# ======================================================================================


def converta_unidade_medida(row, gi_tipo, ca, cl):
    """Converte unidade de medida conforme coeficientes passados por paramentro. Esta
    funcao preve fornecimento de valor a ser convertido igual a bad values. Nesse caso,
    o valor eh convertido para vazio (np.nan).

    Args:
        row (Series): Linha de Dataframe com no minimo a coluna "valor", cujo tipo 
        esperado eh str.
        gi_tipo (bool): Tipo da grandeza industrial para a qual se quer converter
        unidade de medida. Se True, significa que se trata de uma grandeza industrial do 
        tipo estado. Caso contrário, significa que se trata de uma grandeza industrial 
        do tipo float convencial.
        ca (float): Coeficiente angular que deve ser multiplicado pelo valor a ser
        convertido. Quando gi_tipo eh True, espera-se apenas 1.0 ou -1.0 como ca. Sendo
        que 1.0 determina manutencao do valor (conversao desnecessaria) e -1.0
        determina inversao do valor ("1.0" para 0 ou "0" para 1.0). Caso contrario, o
        valor eh convertido para vazio (np.nan). Importante destacar que 
        independentemente do ca valor "0.5" sempre eh convertido para 0.5.
        cl (float): Coeficiente linear que deve ser somado ao valor a ser convertido.
        Quando gi_tipo eh True, cl eh ignorado.

    Returns:
        float: Valor convertido.
    """
    try:
        x = row["valor"]
        if gi_tipo:
            # Tipo estado
            if ca == 1.0:
                r = float(x)
            elif ca == -1.0:
                r = (
                    0
                    if x == "1.0"
                    else 1.0 if x == "0" else 0.5 if x == "0.5" else np.nan
                )
            else:
                r = np.nan
        else:
            # Tipo float convencional
            r = ca * float(x) + cl
    except:
        r = np.nan

    return r


# ======================================================================================
# SECAO PRINCIPAL DESTE SCRIPT
# ======================================================================================

if __name__ == "__main__":
    # Mensagem inicial
    logging.info("iniciando execucao do script exportador...")

    # Cria hash com relacoes entre grandeza_especialista e
    # periodo_amostra_inicial_nao_rotulada
    grandezas_especialistas = grandeza_especialista.objects.all()
    periodos_ainr = {}
    for ge in grandezas_especialistas:
        periodos_ainr[ge.id] = ge.periodo_amostra_inicial_nao_rotulada

    while True:
        # Obtem do banco de dados instancias (analises) marcadas para serem exportadas
        # em ordem crescente em relacao a data_inicio
        analises = (
            analise.objects.filter(exportacao_habilitada=True)
            .filter(status_exportacao="Pendente")
            .order_by("data_inicio")
        )
        num_analises = len(analises)
        if num_analises > 0:
            ids = [a.id for a in analises]
            logging.info(
                "# instancias pendentes de exportacao: {} {}".format(num_analises, ids)
            )

        # Varre cada analise como analise_corr
        for analise_corr in analises:
            logging.info("iniciando exportacao da instancia {}".format(analise_corr.id))

            # Atualiza status_exportacao da analise_corr para "Exportando"
            analise_corr.status_exportacao = "Exportando"
            analise_corr.save()

            # Obtem amostras da analise_corr em ordem crescente em relacao a inicio
            amostras = amostra.objects.filter(analise=analise_corr).order_by("inicio")

            # Verifica se analise_corr estah vazia (nao tem ao menos uma amostra)
            num_amostras = len(amostras)
            if num_amostras < 1:
                logging.warning(
                    "a instancia {} nao foi exportada: instancia sem amostras".format(
                        analise_corr.id
                    )
                )

                # Atualiza status_exportacao da analise_corr para "Erro"
                analise_corr.status_exportacao = "Erro"
                analise_corr.save()

                # Continua para a proxima analise na varredura
                continue

            # Transfere atributos de cada amostra para estrutura facil de ser manipulada
            amostras_df = pd.DataFrame(columns=["class", "state", "inicio", "fim"])
            amostras_df = amostras_df.astype(AMOSTRAS_DTYPES)
            for amostra_corr in amostras:
                # Recupera tipo
                if amostra_corr.tipo == "NORMAL":
                    t = analise_corr.grandeza_especialista.rotulo_normalidade
                elif amostra_corr.tipo == "TRANSIENT":
                    t = analise_corr.grandeza_especialista.rotulo_transient
                elif amostra_corr.tipo == "STEADY STATE":
                    t = analise_corr.grandeza_especialista.rotulo_steady_state
                else:
                    t = np.nan
                # Recupera estado_poco
                estado_poco = ESTADOS_POCO[amostra_corr.estado_poco]
                # Cria e concatena no final da estrutura (DataFrame) linha com atributos
                # da amostra_corr
                amostra_dict = {
                    "class": [t],
                    "state": [estado_poco],
                    "inicio": [amostra_corr.inicio],
                    "fim": [amostra_corr.fim],
                }
                amostras_df = pd.concat(
                    [amostras_df, pd.DataFrame(amostra_dict).astype(AMOSTRAS_DTYPES)],
                    ignore_index=True,
                )

            # Cria e concatena no inicio da estrutura (DataFrame) linha com atributos de
            # amostra inicial nao rotulada, se cabivel
            painr = periodos_ainr[analise_corr.grandeza_especialista.id]
            if painr > 0:
                fim_ainr = amostras_df.iloc[0]["inicio"]
                inicio_ainr = fim_ainr - datetime.timedelta(seconds=painr)
                amostra_dict = {
                    "class": [np.nan],  # Propositalmente sem rotulo
                    "state": [np.nan],  # Propositalmente sem rotulo
                    "inicio": [inicio_ainr],
                    "fim": [fim_ainr],
                }
                amostras_df = pd.concat(
                    [pd.DataFrame(amostra_dict).astype(AMOSTRAS_DTYPES), amostras_df],
                    ignore_index=True,
                )

            # Utiliza span adequado definido em constante em funcao da grandeza
            # especialista da analise corrente
            exploracao = analise_corr.grandeza_especialista.nome == "Exploration"
            if exploracao:
                span = SPAN_EXPLORATION
                freq = FREQ_EXPLORATION
            else:
                span = SPAN_DEFAULT
                freq = FREQ_DEFAULT

            # Obtem inicio (da primeira amostra) e fim (da ultima amostra) para
            # exportacao de valores interpolados a partir de PI System. Todas as
            # observacoes de todas as amostras de cada grandeza industrial da
            # analise_corr sao solicitadas de uma soh vez para aumentar eficiencia.
            # Portanto, o inicio da exportacao eh o inicio da primeira amostra e o fim
            # da exportacao eh o fim da ultima amostra
            inicio_exportacao_corr = str(amostras_df.iloc[0]["inicio"])
            fim_exportacao_corr = str(amostras_df.iloc[-1]["fim"])

            # Gera DataFrame no qual serao armazenadas 100% das informacoes a serem
            # exportadas. A principio, armazena-se apenas timestamps como index desse
            # DataFrame e em formato que facilita slices (selecao de observacoes)
            timestamps = pd.date_range(
                start=inicio_exportacao_corr, end=fim_exportacao_corr, freq=freq
            )
            df = pd.DataFrame(timestamps, columns=["timestamp"])
            df.set_index("timestamp", inplace=True)

            # Varre cada grandeza industrial como gi_corr, que eh obtido de gi_str
            for gi_str, gi_tipo in TIPOS_GRANDEZAS_INDUSTRIAIS.items():
                try:
                    gi_corr = grandeza_industrial.objects.get(nome=gi_str)
                except:
                    logging.warning(
                        (
                            "serie temporal exportada como vazia: a grandeza "
                            + "industrial {} nao estah configurada no GIDEAO"
                        ).format(gi_str)
                    )

                    # Adiciona coluna vazia
                    df[gi_str] = np.nan

                    # Continua para a proxima grandeza industrial na varredura
                    continue

                # Obtem a variavel industrial corrente da grandeza industrial corrente
                # no poco referenciado pela instancia corrente
                # ATENCAO: o metodo filter retornar QuerySet possivelmente vazio ou com
                # multiplos resultados (variaveis industriais). Busca-se utilizar o
                # primeiro resultado (primeira variavel industrial). Quando esse retorno
                # eh vazio, valores interpolados nao sao requisitados ao PI System e a
                # coluna referente a variavel industrial corrente fica complementamente
                # vazia no DataFrame
                vis = variavel_industrial.objects.filter(poco=analise_corr.poco).filter(
                    grandeza_industrial=gi_corr
                )
                num_vis = len(vis)
                if num_vis < 1:
                    logging.warning(
                        (
                            "serie temporal exportada como vazia: nao hah variavel "
                            + "industrial para a grandeza industrial {} configurada "
                            + "no GIDEAO"
                        ).format(gi_str)
                    )

                    # Adiciona coluna vazia
                    df[gi_str] = np.nan
                else:
                    # Alerta eventual replicacao de configuracao de variavel industrial
                    if num_vis > 1:
                        logging.warning(
                            (
                                "existem {} variaveis industriais para {} em {}: foi "
                                + "utilizada a primeira delas"
                            ).format(num_vis, gi_str, analise_corr.poco)
                        )

                    # Utiliza-se a primeira variavel industrial como corrente (premissa)
                    vi_corr = vis[0]

                    # A partir da variavel industrial corrente, obtem o nome da tag e a
                    # conexao correta com o servidor PI ou AF
                    tag_corr = vi_corr.tag.strip()
                    servidor_corr = vi_corr.servidor_pi.strip()
                    if not tag_corr or not servidor_corr:
                        logging.warning(
                            (
                                "serie temporal exportada como vazia: a variavel "
                                + "industrial {} nao estah 100% configurada no GIDEAO"
                            ).format(vi_corr.nome)
                        )

                        # Adiciona coluna vazia
                        df[gi_str] = np.nan

                        # Continua para a proxima grandeza industrial na varredura
                        continue
                    else:
                        conexao_corr = servidores[servidor_corr]

                    # Obtem valores interpolados para a variavel industrial corrente
                    um_padrao_corr = vi_corr.um.unidade_medida_padrao
                    estadosDiscretos = str(um_padrao_corr) == "discreta"
                    val_inter_df = gp.getValoresInterpolados(
                        conexao_corr,
                        tag_corr,
                        inicio_exportacao_corr,
                        fim_exportacao_corr,
                        span,
                        estadosDiscretos,
                    )

                    # Quando os valores interpolados para a variavel industrial corrente
                    # sao obtidos com sucesso e quando a sua unidade de medida estah
                    # 100% configurada, seus valores sao convertidos para assumirem a
                    # unidade de medida padrao no 3W dataset. O resultado dessa
                    # conversao eh adicionado em coluna propria no DataFrame. Quando ela
                    # nao pode ser realizada, a coluna referente a variavel industrial
                    # corrente fica completamente vazia no DataFrame
                    ca_corr = vi_corr.um.coeficiente_angular
                    cl_corr = vi_corr.um.coeficiente_linear
                    if isinstance(val_inter_df, pd.DataFrame):
                        if ca_corr is None or cl_corr is None or um_padrao_corr is None:
                            logging.warning(
                                (
                                    "serie temporal exportada como vazia: a unidade de "
                                    + "medida '{}' (utilizada pela variavel industrial "
                                    + "{}) nao estah 100% configurada no GIDEAO"
                                ).format(vi_corr.um.nome, vi_corr.nome)
                            )

                            # Adiciona coluna vazia
                            df[gi_str] = np.nan
                        else:
                            # Padroniza index de val_inter_df em relacao ao do df
                            val_inter_df.set_index("timestamp", inplace=True)
                            val_inter_df.index = pd.to_datetime(val_inter_df.index)

                            # Gera DataFrame corrente que recebe valores convertidos
                            # OBS: esse jah recebe a coluna que serah juntada no df
                            val_inter_conv_df = pd.DataFrame(columns=[gi_str])

                            # Converte unidade de medida
                            val_inter_conv_df[gi_str] = val_inter_df.apply(
                                converta_unidade_medida,
                                gi_tipo=gi_tipo,
                                ca=ca_corr,
                                cl=cl_corr,
                                axis=1,
                            )

                            # Trata eventuais timestamps replicados
                            # OBS: esse cenario acontece, por exemplo, em encerramento
                            # de horario de verao quando o servidor PI System tem
                            # horario atrasado. Isso porque getValoresInterpolados
                            # entrega timestamps arquivados sem tratamento. Apos
                            # ampla avaliacao, optou-se por enquanto em nao exportar
                            # series temporais (possivelmente instancias inteiras)
                            # com timestamps replicados. A principalmente justificativa
                            # eh que o proprio GIDEAO nao apresenta corretamente series
                            # temporais com timestamps replicados. A ideia eh que esse
                            # cenario passe a ser corretamente tratado tanto pelo
                            # GIDEAO quando pelo exportador apos correcoes em ambos os
                            # sistemas. Por enquanto, o exportador "apernas" alertarah
                            # quando variaveis industriais cairem neste cenario
                            num_dup = int(val_inter_conv_df.index.duplicated().sum())
                            if num_dup > 0:
                                logging.warning(
                                    (
                                        "serie temporal exportada como vazia: a "
                                        + "variavel industrial {} tem historico no "
                                        + "servidor com timestamps replicados, "
                                        + "possivelmente por conta de termino de "
                                        + "horario de verao, e o exportador ainda "
                                        + "nao trata esse cenario"
                                    ).format(vi_corr.nome)
                                )

                                # Adiciona coluna vazia
                                df[gi_str] = np.nan

                                # Continua para a proxima grandeza industrial na
                                # varredura
                                continue

                            # Realiza o join
                            # OBS: eventuais timestamps faltantes no val_inter_df
                            # (portanto tambem no val_inter_conv_df) sao naturalmente
                            # tratados pelo join com df na esquerda. Esse cenario
                            # acontece, por exemplo, em inicio de horario de verao
                            # quando o servidor PI System tem horario adiantado.
                            # Isso porque getValoresInterpolados entrega timestamps
                            # arquivados sem tratamento
                            df = df.join(val_inter_conv_df)
                    else:
                        logging.warning(
                            (
                                "serie temporal exportada como vazia: valores "
                                + "interpolados para a variavel industrial {} nao "
                                + "foram obtidos do servidor"
                            ).format(vi_corr.nome)
                        )

                        # Adiciona coluna vazia
                        df[gi_str] = np.nan

            # Verifica se todas as colunas foram adicionadas como vazias
            if df[GRANDEZAS_INDUSTRIAIS].isnull().all().all():
                logging.warning(
                    (
                        "a instancia {} nao foi exportada: todas as suas series "
                        + "temporais foram exportadas como vazias"
                    ).format(analise_corr.id)
                )

                # Atualiza status_exportacao da analise_corr para "Erro"
                analise_corr.status_exportacao = "Erro"
                analise_corr.save()

                # Continua para a proxima analise na varredura
                continue

            # Se a grandeza especialista da analise corrente nao for do tipo
            # Exploration, adiciona uma coluna com rotulos de observacoes e outra coluna
            # com estados do poco. Isso eh feito a cada amostra em funcao do seu inicio
            # e fim
            if not exploracao:
                for _, row in amostras_df.iterrows():
                    slice_corr = slice(row["inicio"], row["fim"])
                    df.loc[slice_corr, "class"] = row["class"]
                    df.loc[slice_corr, "state"] = row["state"]

            # Salva dados do DataFrame em arquivo apropriado em diretorio apropriado
            # OBS: diretorio esse que eh criado conforme necessidade
            if exploracao:
                sdir = "exploration"
            else:
                sdir = str(analise_corr.grandeza_especialista.rotulo_steady_state)
            dir_exportacao_corr = dir_base_exportacao / sdir
            nome_arquivo_parquet_corr = (
                analise_corr.poco.nome
                + "_"
                + amostras_df.iloc[0]["inicio"].strftime("%Y%m%d%H%M%S")
                + PARQUET_EXTENSION
            )
            path_arquivo_parquet_corr = dir_exportacao_corr / nome_arquivo_parquet_corr
            try:
                dir_exportacao_corr.mkdir(exist_ok=True)
                # Forca padronizacao de tipos a serem exportados em PARQUET
                df = df.astype(PARQUET_DTYPES)  
                df.to_parquet(
                    path_arquivo_parquet_corr,
                    index=True,
                    engine=PARQUET_ENGINE,
                    compression=PARQUET_COMPRESSION,
                )
            except Exception as e:
                # Atualiza status_exportacao da analise_corr para "Erro"
                analise_corr.status_exportacao = "Erro"
                analise_corr.save()

                logging.error("erro ao exportar a instancia {}".format(analise_corr.id))
                raise Exception("erro ao exportar a instancia: {}".format(e))

            # Atualiza status_exportacao da analise_corr para "Exportada"
            analise_corr.status_exportacao = "Exportada"
            analise_corr.save()

            logging.info(
                "concluida exportacao da instancia {} em {}".format(
                    analise_corr.id, path_arquivo_parquet_corr
                )
            )

        # Aguarda um tempo para evitar pooling frequente quando nao houver analises
        # pendentes de exportacao
        time.sleep(30)
