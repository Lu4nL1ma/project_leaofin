import csv
import os
import re
from django.conf import settings  # Importa as configurações do Django
from django.core.management.base import BaseCommand, CommandError
from app_leao.models import Categoria  # Substitua 'seu_app' pelo nome real do seu app


class Command(BaseCommand):
    help = "Importa categorias a partir de um arquivo CSV localizado na raiz do projeto"

    def add_arguments(self, parser):
        # O usuário passa apenas o nome do arquivo (ex: dados.csv)
        parser.add_argument("csv_filename", type=str, help="Nome do arquivo CSV dentro do projeto")

    def handle(self, *args, **options):
        # Monta o caminho dinamicamente combinando a raiz do projeto com o nome do arquivo
        csv_path = os.path.join(settings.BASE_DIR, options["csv_filename"])

        # Verifica se o arquivo realmente existe no caminho montado
        if not os.path.exists(csv_path):
            raise CommandError(f"Arquivo não encontrado em: {csv_path}")

        self.stdout.write(self.style.WARNING(f"Iniciando a leitura de: {csv_path}"))

        categorias_para_criar = []

        # Função auxiliar para limpar ruídos como parênteses vazios e espaços extras
        def limpar_texto(texto):
            if not texto:
                return "-"
            texto_limpo = str(texto).strip()
            # Remove parênteses vazios "()" que possam ter sido injetados erroneamente
            texto_limpo = re.sub(r'\(\s*\)', '', texto_limpo).strip()
            return texto_limpo if texto_limpo else "-"

        with open(csv_path, mode="r", encoding="utf-8-sig") as file:
            # Descobre automaticamente se o separador é vírgula ou ponto e vírgula
            try:
                amostra = file.read(2048)
                dialeto = csv.Sniffer().sniff(amostra, delimiters=[',', ';'])
                file.seek(0)
            except csv.Error:
                # Caso não consiga detectar, assume o padrão de vírgula
                dialeto = 'excel'
                file.seek(0)

            reader = csv.DictReader(file, dialect=dialeto)

            for linha in reader:
                # Captura e limpa os campos individualmente
                nome = limpar_texto(linha.get("nome"))
                grupo = limpar_texto(linha.get("grupo"))
                tipo = limpar_texto(linha.get("tipo"))
                descricao = limpar_texto(linha.get("descricao"))

                # Se o nome for inválido ou apenas o traço padrão, pula a linha
                if not nome or nome == "-":
                    continue

                # Evita duplicar categorias que já existem no banco pelo Nome
                if Categoria.objects.filter(nome=nome).exists():
                    self.stdout.write(
                        self.style.NOTICE(f"Categoria '{nome}' já existe. Pula.")
                    )
                    continue

                categoria = Categoria(
                    nome=nome,
                    grupo=grupo,
                    tipo=tipo,
                    descricao=descricao
                )
                categorias_para_criar.append(categoria)

        # Insere tudo de uma vez de forma performática
        if categorias_para_criar:
            quantidade = len(categorias_para_criar)
            Categoria.objects.bulk_create(categorias_para_criar)
            self.stdout.write(
                self.style.SUCCESS(f"Sucesso! {quantidade} categorias inseridas na tabela.")
            )
        else:
            self.stdout.write(self.style.WARNING("Nenhuma nova categoria para importar."))