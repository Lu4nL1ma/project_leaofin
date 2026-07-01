import csv
import os
from django.conf import settings  # Importa as configurações do Django
from django.core.management.base import BaseCommand, CommandError
from app_leao.models import Categoria  # Substitua 'seu_app' pelo nome real do seu app


class Command(BaseCommand):
    help = "Importa categorias a partir de um arquivo CSV localizado na raiz do projeto"

    def add_arguments(self, parser):
        # Agora o usuário passa apenas o nome do arquivo (ex: dados.csv)
        parser.add_argument("csv_filename", type=str, help="Nome do arquivo CSV dentro do projeto")

    def handle(self, *args, **options):
        # Monta o caminho dinamicamente combinando a raiz do projeto com o nome do arquivo
        csv_path = os.path.join(settings.BASE_DIR, options["csv_filename"])

        # Verifica se o arquivo realmente existe no caminho montado
        if not os.path.exists(csv_path):
            raise CommandError(f"Arquivo não encontrado em: {csv_path}")

        self.stdout.write(self.style.WARNING(f"Iniciando a leitura de: {csv_path}"))

        categorias_para_criar = []
        
        with open(csv_path, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            
            for linha in reader:
                nome = linha.get("nome", "").strip()
                grupo = linha.get("grupo", "").strip()
                tipo = linha.get("tipo", "").strip()
                descricao = inline_descricao = linha.get("descricao", "").strip()

                if not nome:
                    continue  
                
                if Categoria.objects.filter(nome=nome).exists():
                    self.stdout.write(
                        self.style.NOTICE(f"Categoria '{nome}' já existe. Pula.")
                    )
                    continue

                categoria = Categoria(
                    nome=nome or "-",
                    grupo=grupo or "-",
                    tipo=tipo or "-",
                    descricao=descricao or "-"
                )
                categorias_para_criar.append(categoria)

        if categorias_para_criar:
            quantidade = len(categorias_para_criar)
            Categoria.objects.bulk_create(categorias_para_criar)
            self.stdout.write(
                self.style.SUCCESS(f"Sucesso! {quantidade} categorias inseridas na tabela.")
            )
        else:
            self.stdout.write(self.style.WARNING("Nenhuma nova categoria para importar."))