from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import timedelta
from typing import Any
from urllib.parse import urlencode

from django import template
from django.apps import apps
from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.core.cache import cache
from django.db import DatabaseError
from django.db.models import Count
from django.urls import NoReverseMatch, reverse
from django.utils import timezone, translation

register = template.Library()


@register.filter
def get_item(value: dict[str, Any], key: str) -> Any:
    if isinstance(value, dict):
        return value.get(key)
    return None


@register.filter
def aho_ui_label(value: str) -> str:
    return _ui_label(str(value))


UI_LABELS: dict[str, dict[str, str]] = {
    "fr": {
        "Data Capture Tool": "Outil de collecte des donnees",
        "Integrated African Health Observatory data capture platform": "Plateforme integree de collecte des donnees de l'Observatoire africain de la sante",
        "WHO Regional Office for Africa": "Bureau regional de l'OMS pour l'Afrique",
        "Welcome": "Bienvenue",
        "Search": "Rechercher",
        "Language": "Langue",
        "User menu": "Menu utilisateur",
        "Home": "Accueil",
        "Current location": "Localisation actuelle",
        "Main navigation": "Navigation principale",
        "Section navigation": "Navigation de section",
        "Toggle navigation": "Afficher ou masquer le menu",
        "African Region": "Region africaine",
        "Messages": "Messages",
        "Notifications": "Notifications",
        "Received messages": "Messages recus",
        "No recent messages": "Aucun message recent.",
        "View all messages": "Voir tous les messages",
        "System notifications": "Notifications systeme",
        "No pending notifications": "Aucune notification en attente.",
        "View pending items": "Voir les elements en attente",
        "No new messages": "Aucun nouveau message",
        "new message": "nouveau message",
        "new messages": "nouveaux messages",
        "No pending items": "Aucun element en attente",
        "pending item": "element en attente",
        "pending items": "elements en attente",
        "Created": "Cree",
        "Changed": "Modifie",
        "Deleted": "Supprime",
        "Action required": "Action requise",
        "Pending approval": "En attente d'approbation",
        "Theme": "Theme",
        "Compact mode": "Mode compact",
        "Change password": "Changer le mot de passe",
        "Log out": "Deconnexion",
        "Filters": "Filtres",
        "Filter": "Filtrer",
        "Sort": "Trier",
        "Reset filters": "Reinitialiser les filtres",
        "Search records": "Rechercher dans les lignes",
        "No results found.": "Aucun resultat trouve.",
        "No data available yet.": "Aucune donnee disponible pour le moment.",
        "Actions": "Actions",
        "Edit": "Modifier",
        "Approve": "Approuver",
        "Approved": "Approuve",
        "Reject": "Rejeter",
        "Rejected": "Rejete",
        "Pending": "Mettre en attente",
        "Pending status": "En attente",
        "Already selected": "Statut deja selectionne",
        "Delete": "Supprimer",
        "results": "resultats",
        "Previous": "Precedent",
        "Next": "Suivant",
        "Dashboard": "Tableau de bord",
        "Indicators": "Indicateurs",
        "UHC clock": "Horloge CSU",
        "Facilities": "Etablissements",
        "Health workforce": "Personnel de sante",
        "Health services": "Services de sante",
        "Data elements": "Elements de donnees",
        "Publications": "Publications",
        "Locations": "Localisations",
        "Data integration": "Integration des donnees",
        "Data quality": "Qualite des donnees",
        "API tokens": "Jetons API",
        "Active tokens": "Jetons actifs",
        "Endpoint": "Endpoint",
        "Description": "Description",
        "Scope": "Portee",
        "Examples": "Exemples",
        "Export": "Exporter",
        "Columns": "Colonnes",
        "Toggle columns": "Afficher ou masquer les colonnes",
        "Download CSV": "Telecharger CSV",
        "Import data": "Importer les donnees",
        "Add data": "Ajouter les donnees",
        "List": "Liste",
        "Import indicator data": "Importer les donnees indicateurs",
        "Choose file": "Choisir un fichier",
        "Selected file": "Fichier selectionne",
        "No file selected": "Aucun fichier selectionne",
        "Download template": "Telecharger le modele",
        "Indicator import template": "Modele d'import indicateurs",
        "Continue to import wizard": "Continuer vers l'assistant d'import",
        "Close": "Fermer",
        "Rows per page": "Lignes par page",
        "Use the CSV model below, then continue to the import wizard to upload and validate the file.": "Utilisez le modele CSV ci-dessous, puis continuez vers l'assistant d'import pour charger et valider le fichier.",
        "Provider": "Fournisseur",
        "Method": "Methode",
        "Server name": "Nom du serveur",
        "API URL": "URL API",
        "Sync frequency": "Frequence de synchronisation",
        "Last test status": "Dernier statut de test",
        "Field mappings": "Correspondances de champs",
        "Last synced at": "Derniere synchronisation",
        "Modified": "Modification",
        "Dataset source": "Source du jeu de donnees",
        "Current source": "Source actuelle",
        "Fact indicator data": "Donnees indicateurs",
        "Data quality view": "Vue qualite des donnees",
        "Django DCT": "Django DCT",
        "Custom": "Personnalise",
        "Direct": "Direct",
        "API": "API",
        "Manual": "Manuel",
        "Active": "Actif",
        "Validated": "Valide",
        "Failed": "Echec",
        "API documentation": "Documentation API",
        "List indicators": "Lister les indicateurs",
        "List indicator values": "Lister les valeurs indicateurs",
        "Create indicator value": "Creer une valeur indicateur",
        "Update indicator value": "Modifier une valeur indicateur",
        "Delete indicator value": "Supprimer une valeur indicateur",
        "List indicator archives": "Lister les archives indicateurs",
        "List data sources": "Lister les sources de donnees",
        "List measure types": "Lister les types de mesure",
        "Generate DRF auth token": "Generer un jeton DRF",
        "Read": "Lecture",
        "Write": "Ecriture",
        "Create token": "Creer le jeton",
        "Revoke": "Revoquer",
        "Copy": "Copier",
        "Token copied": "Jeton copie",
        "API token is ready. Copy it now and keep it secure.": "Le jeton API est pret. Copiez-le maintenant et conservez-le en securite.",
        "API token revoked.": "Jeton API revoque.",
        "Token was not found or cannot be revoked.": "Le jeton est introuvable ou ne peut pas etre revoque.",
        "Authentication": "Authentification",
        "Data": "Donnees",
        "Data wizard": "Assistant de donnees",
        "References": "References",
        "Sources": "Sources",
        "Indicator values": "Valeurs des indicateurs",
        "Archives": "Archives",
        "Imports": "Imports",
        "Exports": "Exports",
        "Indicator import files": "Fichiers importes des indicateurs",
        "Indicator export files": "Fichiers exportes des indicateurs",
        "Excel and CSV files used for indicator data imports.": "Fichiers Excel et CSV utilises pour importer les donnees indicateurs.",
        "Export history is shown when available; otherwise the table lists indicator source files available for export.": "L'historique des exports est affiche lorsqu'il existe ; sinon le tableau liste les fichiers sources indicateurs disponibles pour l'export.",
        "Import runs": "Lots importes",
        "Imported rows": "Lignes importees",
        "Failed rows": "Lignes echouees",
        "Indicators": "Indicateurs",
        "Indicator domains": "Domaines d'indicateurs",
        "Indicator references": "References des indicateurs",
        "Disaggregation categories": "Categories de desagregation",
        "Disaggregation options": "Options de desagregation",
        "Measure methods": "Methodes de mesure",
        "Periods": "Periodes",
        "Value types": "Types de valeur",
        "Narrative types": "Types narratifs",
        "Theme narratives": "Narratifs des themes",
        "Indicator narratives": "Narratifs des indicateurs",
        "Themes lookup": "Correspondance des themes",
        "Custom icons": "Icones personnalisees",
        "UHC facts": "Donnees CSU",
        "Priority indicators": "Indicateurs prioritaires",
        "UHC groups": "Groupes CSU",
        "UHC indicators": "Indicateurs CSU",
        "UHC themes": "Themes CSU",
        "UHC country selections": "Selections pays CSU",
        "Health facilities": "Etablissements de sante",
        "Service capacity": "Capacite de service",
        "Service readiness": "Preparation des services",
        "Services availability": "Disponibilite des services",
        "Facility owners": "Proprietaires",
        "Facility types": "Types d'etablissements",
        "Service areas": "Zones de service",
        "Service domains": "Domaines de service",
        "Service interventions": "Interventions de service",
        "Provision units": "Unites de prestation",
        "Workforce values": "Valeurs du personnel",
        "Resources / guides": "Ressources / guides",
        "Nursing and midwifery": "Soins infirmiers et sages-femmes",
        "Announcements": "Annonces",
        "Health cadres": "Cadres de sante",
        "Training institutions": "Institutions de formation",
        "Institution types": "Types d'institutions",
        "Training programmes": "Programmes de formation",
        "Resource types": "Types de ressources",
        "Resource categories": "Categories de ressources",
        "Service values": "Valeurs des services",
        "HSC indicators": "Indicateurs HSC",
        "HSC programmes": "Programmes HSC",
        "HSC programmes lookup": "Correspondance des programmes HSC",
        "Data element values": "Valeurs des elements",
        "Data elements": "Elements de donnees",
        "Data element groups": "Groupes d'elements",
        "Knowledge products": "Produits de connaissance",
        "Publication domains": "Domaines de publication",
        "Resource tags": "Etiquettes de ressources",
        "Locations": "Localisations",
        "Level 2 locations": "Localisations niveau 2",
        "Location levels": "Niveaux de localisation",
        "Income groups": "Groupes de revenu",
        "Economic blocks": "Blocs economiques",
        "Special categorizations": "Categorisations speciales",
        "Dial codes": "Indicatifs telephoniques",
        "National observatories": "Observatoires nationaux",
        "Connections": "Connexions",
        "Failed rows": "Lignes echouees",
        "Indicator checks": "Controles des indicateurs",
        "Indicator value controls": "Controles des valeurs indicateurs",
        "Review records that may need correction before approval or publication.": "Passez en revue les enregistrements a corriger avant approbation ou publication.",
        "Quality filters": "Filtres qualite",
        "All alerts": "Toutes les alertes",
        "Errors": "Erreurs",
        "Warnings": "Alertes",
        "Error": "Erreur",
        "Warning": "Alerte",
        "Checked sample": "Echantillon controle",
        "Latest quality alerts": "Dernieres alertes qualite",
        "Filter by severity or search by indicator, country, period, value, rule, or message.": "Filtrez par severite ou recherchez par indicateur, pays, periode, valeur, regle ou message.",
        "The table shows the latest detected issues first.": "Le tableau affiche d'abord les dernieres anomalies detectees.",
        "Rule": "Regle",
        "Severity": "Severite",
        "Message": "Message",
        "Correct": "Corriger",
        "Search in quality issues...": "Rechercher dans les problemes de qualite...",
        "Clear": "Effacer",
        "No issue found in the latest checked records.": "Aucun probleme trouve dans les derniers enregistrements controles.",
        "No alert matches the current filter.": "Aucune alerte ne correspond au filtre actuel.",
        "result displayed": "resultat affiche",
        "results displayed": "resultats affiches",
        "Facts dataset": "Jeu de donnees factuelles",
        "Facts filter": "Filtre des donnees",
        "Category options": "Options de categorie",
        "Datasources": "Sources de donnees",
        "Measure types": "Types de mesure",
        "Check categories": "Controle des categories",
        "Check measures": "Controle des mesures",
        "Check periods": "Controle des periodes",
        "Check sources": "Controle des sources",
        "External consistencies": "Coherences externes",
        "Internal consistencies": "Coherences internes",
        "Missing values": "Valeurs manquantes",
        "Similarity scores": "Scores de similarite",
        "Multiple measures": "Mesures multiples",
        "Value type checks": "Controles des types de valeur",
        "Token status": "Statut des jetons",
        "Users": "Utilisateurs",
        "Roles": "Roles",
        "Permissions": "Permissions",
        "User history": "Historique utilisateur",
        "Values": "Valeurs",
        "Archive": "Archive",
        "Sources / methods": "Sources / methodes",
        "Sources / methods / categories": "Sources / methodes / categories",
        "Level 2 locations: {count}": "Localisations niveau 2 : {count}",
        "Indicators with values: {count}": "Indicateurs avec valeurs : {count}",
        "Approved: {approved} | Pending: {pending} | Rejected: {rejected}": "Approuvees : {approved} | En attente : {pending} | Rejetees : {rejected}",
        "Values from fact_data_archive": "Valeurs provenant de fact_data_archive",
        "Available data sources and measure methods": "Sources de donnees et methodes de mesure disponibles",
        "Data sources / measure methods / categories": "Sources de donnees / methodes de mesure / categories",
        "Registered application accounts": "Comptes utilisateurs enregistres",
        "Recent indicator uploads": "Indicateurs recemment charges",
        "Top 5 recently loaded indicators": "Top 5 des indicateurs recemment charges",
        "Top 5 indicators used for the African Region": "Top 5 des indicateurs utilises pour la region africaine",
        "Top 5 indicators loaded by countries": "Top 5 des indicateurs charges par les pays",
        "Top 5 data sources used": "Top 5 des sources de donnees utilisees",
        "Indicator values by period": "Valeurs des indicateurs par periode",
        "Active + archived records": "Donnees actives + archivees",
    },
    "pt": {
        "Data Capture Tool": "Ferramenta de captura de dados",
        "Integrated African Health Observatory data capture platform": "Plataforma integrada de captura de dados do Observatorio Africano da Saude",
        "WHO Regional Office for Africa": "Escritorio Regional da OMS para a Africa",
        "Welcome": "Bem-vindo",
        "Search": "Pesquisar",
        "Language": "Idioma",
        "User menu": "Menu do utilizador",
        "Home": "Inicio",
        "Current location": "Localizacao atual",
        "Main navigation": "Navegacao principal",
        "Section navigation": "Navegacao da seccao",
        "Toggle navigation": "Mostrar ou ocultar o menu",
        "African Region": "Regiao Africana",
        "Messages": "Mensagens",
        "Notifications": "Notificacoes",
        "Received messages": "Mensagens recebidas",
        "No recent messages": "Nenhuma mensagem recente.",
        "View all messages": "Ver todas as mensagens",
        "System notifications": "Notificacoes do sistema",
        "No pending notifications": "Nenhuma notificacao pendente.",
        "View pending items": "Ver itens pendentes",
        "No new messages": "Nenhuma mensagem nova",
        "new message": "mensagem nova",
        "new messages": "mensagens novas",
        "No pending items": "Nenhum item pendente",
        "pending item": "item pendente",
        "pending items": "itens pendentes",
        "Created": "Criado",
        "Changed": "Modificado",
        "Deleted": "Eliminado",
        "Action required": "Acao necessaria",
        "Pending approval": "Pendente de aprovacao",
        "Theme": "Tema",
        "Compact mode": "Modo compacto",
        "Change password": "Alterar palavra-passe",
        "Log out": "Terminar sessao",
        "Filters": "Filtros",
        "Filter": "Filtrar",
        "Sort": "Ordenar",
        "Reset filters": "Repor filtros",
        "Search records": "Pesquisar registos",
        "No results found.": "Nenhum resultado encontrado.",
        "No data available yet.": "Ainda nao ha dados disponiveis.",
        "Actions": "Acoes",
        "Edit": "Editar",
        "Approve": "Aprovar",
        "Approved": "Aprovado",
        "Reject": "Rejeitar",
        "Rejected": "Rejeitado",
        "Pending": "Pendente",
        "Pending status": "Pendente",
        "Already selected": "Estado ja selecionado",
        "Delete": "Eliminar",
        "results": "resultados",
        "Previous": "Anterior",
        "Next": "Seguinte",
        "Dashboard": "Painel",
        "Indicators": "Indicadores",
        "UHC clock": "Relogio CSU",
        "Facilities": "Unidades de saude",
        "Health workforce": "Forca de trabalho em saude",
        "Health services": "Servicos de saude",
        "Data elements": "Elementos de dados",
        "Publications": "Publicacoes",
        "Locations": "Localizacoes",
        "Data integration": "Integracao de dados",
        "Data quality": "Qualidade dos dados",
        "API tokens": "Tokens API",
        "Active tokens": "Tokens ativos",
        "Endpoint": "Endpoint",
        "Description": "Descricao",
        "Scope": "Ambito",
        "Examples": "Exemplos",
        "Export": "Exportar",
        "Columns": "Colunas",
        "Toggle columns": "Mostrar ou ocultar colunas",
        "Download CSV": "Transferir CSV",
        "Import data": "Importar dados",
        "Add data": "Adicionar dados",
        "List": "Lista",
        "Import indicator data": "Importar dados dos indicadores",
        "Choose file": "Escolher ficheiro",
        "Selected file": "Ficheiro selecionado",
        "No file selected": "Nenhum ficheiro selecionado",
        "Download template": "Transferir modelo",
        "Indicator import template": "Modelo de importacao de indicadores",
        "Continue to import wizard": "Continuar para o assistente de importacao",
        "Close": "Fechar",
        "Rows per page": "Linhas por pagina",
        "Use the CSV model below, then continue to the import wizard to upload and validate the file.": "Use o modelo CSV abaixo e continue para o assistente de importacao para carregar e validar o ficheiro.",
        "Provider": "Fornecedor",
        "Method": "Metodo",
        "Server name": "Nome do servidor",
        "API URL": "URL da API",
        "Sync frequency": "Frequencia de sincronizacao",
        "Last test status": "Ultimo estado do teste",
        "Field mappings": "Mapeamentos de campos",
        "Last synced at": "Ultima sincronizacao",
        "Modified": "Modificado",
        "Dataset source": "Fonte do conjunto de dados",
        "Current source": "Fonte atual",
        "Fact indicator data": "Dados factuais dos indicadores",
        "Data quality view": "Vista de qualidade dos dados",
        "Django DCT": "Django DCT",
        "Custom": "Personalizado",
        "Direct": "Direto",
        "API": "API",
        "Manual": "Manual",
        "Active": "Ativo",
        "Validated": "Validado",
        "Failed": "Falhou",
        "API documentation": "Documentacao da API",
        "List indicators": "Listar indicadores",
        "List indicator values": "Listar valores dos indicadores",
        "Create indicator value": "Criar valor do indicador",
        "Update indicator value": "Atualizar valor do indicador",
        "Delete indicator value": "Eliminar valor do indicador",
        "List indicator archives": "Listar arquivos dos indicadores",
        "List data sources": "Listar fontes de dados",
        "List measure types": "Listar tipos de medida",
        "Generate DRF auth token": "Gerar token DRF",
        "Read": "Leitura",
        "Write": "Escrita",
        "Create token": "Criar token",
        "Revoke": "Revogar",
        "Copy": "Copiar",
        "Token copied": "Token copiado",
        "API token is ready. Copy it now and keep it secure.": "O token API esta pronto. Copie-o agora e guarde-o em seguranca.",
        "API token revoked.": "Token API revogado.",
        "Token was not found or cannot be revoked.": "O token nao foi encontrado ou nao pode ser revogado.",
        "Authentication": "Autenticacao",
        "Data": "Dados",
        "Data wizard": "Assistente de dados",
        "References": "Referencias",
        "Sources": "Fontes",
        "Indicator values": "Valores dos indicadores",
        "Archives": "Arquivos",
        "Imports": "Importacoes",
        "Exports": "Exportacoes",
        "Indicator import files": "Ficheiros importados dos indicadores",
        "Indicator export files": "Ficheiros exportados dos indicadores",
        "Excel and CSV files used for indicator data imports.": "Ficheiros Excel e CSV usados para importar dados dos indicadores.",
        "Export history is shown when available; otherwise the table lists indicator source files available for export.": "O historico de exportacao e mostrado quando disponivel; caso contrario, a tabela lista os ficheiros fonte dos indicadores disponiveis para exportacao.",
        "Import runs": "Lotes importados",
        "Imported rows": "Linhas importadas",
        "Failed rows": "Linhas com falha",
        "Indicator domains": "Dominios dos indicadores",
        "Indicator references": "Referencias dos indicadores",
        "Disaggregation categories": "Categorias de desagregacao",
        "Disaggregation options": "Opcoes de desagregacao",
        "Measure methods": "Metodos de medida",
        "Periods": "Periodos",
        "Value types": "Tipos de valor",
        "UHC facts": "Dados CSU",
        "Priority indicators": "Indicadores prioritarios",
        "UHC groups": "Grupos CSU",
        "UHC indicators": "Indicadores CSU",
        "UHC themes": "Temas CSU",
        "UHC country selections": "Selecoes de pais CSU",
        "Health facilities": "Unidades de saude",
        "Service capacity": "Capacidade de servico",
        "Service readiness": "Prontidao dos servicos",
        "Services availability": "Disponibilidade dos servicos",
        "Workforce values": "Valores da forca de trabalho",
        "Resources / guides": "Recursos / guias",
        "Health cadres": "Quadros de saude",
        "Training institutions": "Instituicoes de formacao",
        "Training programmes": "Programas de formacao",
        "Service values": "Valores dos servicos",
        "Data element values": "Valores dos elementos",
        "Knowledge products": "Produtos de conhecimento",
        "Connections": "Conexoes",
        "Failed rows": "Linhas com falha",
        "Indicator checks": "Verificacoes dos indicadores",
        "Indicator value controls": "Controlos dos valores dos indicadores",
        "Review records that may need correction before approval or publication.": "Reveja os registos que podem precisar de correcao antes da aprovacao ou publicacao.",
        "Quality filters": "Filtros de qualidade",
        "All alerts": "Todos os alertas",
        "Errors": "Erros",
        "Warnings": "Alertas",
        "Error": "Erro",
        "Warning": "Alerta",
        "Checked sample": "Amostra verificada",
        "Latest quality alerts": "Ultimos alertas de qualidade",
        "Filter by severity or search by indicator, country, period, value, rule, or message.": "Filtre por gravidade ou pesquise por indicador, pais, periodo, valor, regra ou mensagem.",
        "The table shows the latest detected issues first.": "A tabela mostra primeiro os problemas mais recentes.",
        "Rule": "Regra",
        "Severity": "Gravidade",
        "Message": "Mensagem",
        "Correct": "Corrigir",
        "Search in quality issues...": "Pesquisar nos problemas de qualidade...",
        "Clear": "Limpar",
        "No issue found in the latest checked records.": "Nenhum problema encontrado nos ultimos registos verificados.",
        "No alert matches the current filter.": "Nenhum alerta corresponde ao filtro atual.",
        "result displayed": "resultado apresentado",
        "results displayed": "resultados apresentados",
        "Facts dataset": "Conjunto de dados factuais",
        "Facts filter": "Filtro de dados",
        "Category options": "Opcoes de categoria",
        "Datasources": "Fontes de dados",
        "Measure types": "Tipos de medida",
        "External consistencies": "Consistencias externas",
        "Internal consistencies": "Consistencias internas",
        "Missing values": "Valores em falta",
        "Token status": "Estado dos tokens",
        "Users": "Utilizadores",
        "Roles": "Funcoes",
        "Permissions": "Permissoes",
        "User history": "Historico do utilizador",
        "Level 2 locations: {count}": "Localizacoes de nivel 2: {count}",
        "Indicators with values: {count}": "Indicadores com valores: {count}",
        "Approved: {approved} | Pending: {pending} | Rejected: {rejected}": "Aprovados: {approved} | Pendentes: {pending} | Rejeitados: {rejected}",
        "Values from fact_data_archive": "Valores de fact_data_archive",
        "Available data sources and measure methods": "Fontes de dados e metodos de medida disponiveis",
        "Sources / methods / categories": "Fontes / metodos / categorias",
        "Data sources / measure methods / categories": "Fontes de dados / metodos de medida / categorias",
        "Registered application accounts": "Contas de utilizador registadas",
        "Recent indicator uploads": "Indicadores carregados recentemente",
        "Top 5 recently loaded indicators": "Top 5 indicadores carregados recentemente",
        "Top 5 indicators used for the African Region": "Top 5 indicadores usados na Regiao Africana",
        "Top 5 indicators loaded by countries": "Top 5 indicadores carregados pelos paises",
        "Top 5 data sources used": "Top 5 fontes de dados usadas",
        "Indicator values by period": "Valores dos indicadores por periodo",
        "Active + archived records": "Dados ativos + arquivados",
    },
}


def _ui_label(label: str) -> str:
    lang = (translation.get_language() or "en").split("-", 1)[0]
    return UI_LABELS.get(lang, {}).get(label, label)


def _item(label: str, model: str | None = None, url_name: str | None = None) -> dict[str, Any]:
    return {"label": label, "model": model, "url_name": url_name}


# This menu mirrors the Laravel/Filament navigation order and grouping. Each
# item points to the closest Django admin model already registered in this app.
LARAVEL_MENU: list[dict[str, Any]] = [
    {
        "label": "Indicators",
        "icon": "indicators",
        "groups": [
            {
                "label": "Data",
                "items": [
                    _item("Indicator values", "indicators.FactDataIndicator"),
                    _item("Archives", "indicators.aho_factsindicator_archive"),
                ],
            },
            {
                "label": "Data wizard",
                "items": [
                    _item("Imports", url_name="aho_indicator_imports"),
                    _item("Exports", url_name="aho_indicator_exports"),
                ],
            },
            {
                "label": "References",
                "items": [
                    _item("Indicators", "indicators.StgIndicator"),
                    _item("Indicator domains", "indicators.StgIndicatorDomain"),
                    _item("Indicator references", "indicators.StgIndicatorReference"),
                    _item("Disaggregation categories", "home.StgCategoryParent"),
                    _item("Disaggregation options", "home.StgCategoryoption"),
                    _item("Sources", "home.StgDatasource"),
                    _item("Measure methods", "home.StgMeasuremethod"),
                    _item("Periods", "home.StgPeriodType"),
                    _item("Value types", "home.StgValueDatatype"),
                    _item("Narrative types", "indicators.StgNarrative_Type"),
                    _item("Theme narratives", "indicators.StgAnalyticsNarrative"),
                    _item("Indicator narratives", "indicators.StgIndicatorNarrative"),
                    _item("Themes lookup", "indicators.AhoDoamain_Lookup"),
                    _item("Custom icons", "indicators.NHOCustomizationIcons"),
                ],
            },
        ],
    },
    {
        "label": "UHC clock",
        "icon": "clock",
        "groups": [
            {
                "label": "Data",
                "items": [
                    _item("UHC facts", "uhc_clock.Facts_UHC_DatabaseView"),
                    _item("Priority indicators", "indicators.NHOCustomFactsindicator"),
                ],
            },
            {
                "label": "References",
                "items": [
                    _item("UHC groups", "uhc_clock.StgUHClockIndicatorsGroup"),
                    _item("UHC indicators", "uhc_clock.StgUHClockIndicators"),
                    _item("UHC themes", "uhc_clock.StgUHCIndicatorTheme"),
                    _item("UHC country selections", "uhc_clock.CountrySelectionUHCIndicators"),
                ],
            },
        ],
    },
    {
        "label": "Facilities",
        "icon": "facilities",
        "groups": [
            {
                "label": "Data",
                "items": [
                    _item("Health facilities", "facilities.StgHealthFacility"),
                    _item("Service capacity", "facilities.FacilityServiceProvisionProxy"),
                    _item("Service readiness", "facilities.FacilityServiceReadinesProxy"),
                    _item("Services availability", "facilities.FacilityServiceAvailabilityProxy"),
                ],
            },
            {
                "label": "References",
                "items": [
                    _item("Facility owners", "facilities.StgFacilityOwnership"),
                    _item("Facility types", "facilities.StgFacilityType"),
                    _item("Service areas", "facilities.StgFacilityServiceAreas"),
                    _item("Service domains", "facilities.StgServiceDomain"),
                    _item("Service interventions", "facilities.StgFacilityServiceIntervention"),
                    _item("Provision units", "facilities.StgFacilityServiceMeasureUnits"),
                ],
            },
        ],
    },
    {
        "label": "Health workforce",
        "icon": "workforce",
        "groups": [
            {
                "label": "Data",
                "items": [
                    _item("Workforce values", "health_workforce.StgHealthWorkforceFacts"),
                    _item("Resources / guides", "health_workforce.HumanWorkforceResourceProxy"),
                    _item("Nursing and midwifery", "health_workforce.StgRecurringEvent"),
                    _item("Announcements", "health_workforce.StgAnnouncements"),
                ],
            },
            {
                "label": "References",
                "items": [
                    _item("Health cadres", "health_workforce.StgHealthCadre"),
                    _item("Training institutions", "health_workforce.StgTrainingInstitution"),
                    _item("Institution types", "health_workforce.StgInstitutionType"),
                    _item("Training programmes", "health_workforce.StgInstitutionProgrammes"),
                    _item("Resource types", "health_workforce.ResourceTypeProxy"),
                    _item("Resource categories", "health_workforce.ResourceCategoryProxy"),
                ],
            },
        ],
    },
    {
        "label": "Health services",
        "icon": "services",
        "groups": [
            {
                "label": "Data",
                "items": [_item("Service values", "health_services.HealthServices_DataIndicators")],
            },
            {
                "label": "References",
                "items": [
                    _item("HSC indicators", "health_services.HealthServicesIndicators"),
                    _item("HSC programmes", "health_services.HealthServicesProgrammes"),
                    _item("HSC programmes lookup", "health_services.HSCPrograms_Lookup"),
                ],
            },
        ],
    },
    {
        "label": "Data elements",
        "icon": "elements",
        "groups": [
            {
                "label": "Data",
                "items": [_item("Data element values", "elements.FactDataElement")],
            },
            {
                "label": "References",
                "items": [
                    _item("Data elements", "elements.StgDataElement"),
                    _item("Data element groups", "elements.StgDataElementGroup"),
                ],
            },
        ],
    },
    {
        "label": "Publications",
        "icon": "publications",
        "groups": [
            {
                "label": "Data",
                "items": [_item("Knowledge products", "publications.StgKnowledgeProduct")],
            },
            {
                "label": "References",
                "items": [
                    _item("Resource types", "publications.StgResourceType"),
                    _item("Resource categories", "publications.StgResourceCategory"),
                    _item("Publication domains", "publications.StgProductDomain"),
                    _item("Resource tags", "publications.StgKnowledgeResourceTagging"),
                ],
            },
        ],
    },
    {
        "label": "Locations",
        "icon": "locations",
        "groups": [
            {
                "label": "References",
                "items": [
                    _item("Locations", "regions.StgLocation"),
                    _item("Level 2 locations", "regions.StgLocation"),
                    _item("Location levels", "regions.StgLocationLevel"),
                    _item("Income groups", "regions.StgWorldbankIncomegroups"),
                    _item("Economic blocks", "regions.StgEconomicZones"),
                    _item("Special categorizations", "regions.StgSpecialcategorization"),
                    _item("Dial codes", "regions.StgLocationCodes"),
                    _item("National observatories", "home.StgCustomNationalObservatory"),
                ],
            }
        ],
    },
    {
        "label": "Data integration",
        "icon": "integration",
        "groups": [
            {
                "label": "Sources",
                "items": [_item("Connections", url_name="aho_data_integration_connections")],
            }
        ],
    },
    {
        "label": "Data quality",
        "icon": "quality",
        "groups": [
            {
                "label": "Data quality",
                "items": [
                    _item("Indicator checks", url_name="aho_data_quality_indicator_checks"),
                    _item("Facts dataset", url_name="aho_data_quality_facts_dataset"),
                    _item("Facts filter", "data_quality.Facts_DataFilter"),
                    _item("Category options", "data_quality.CategoryOptions_Validator"),
                    _item("Datasources", "data_quality.DataSource_Validator"),
                    _item("Measure types", "data_quality.MeasureTypes_Validator"),
                    _item("Check categories", "data_quality.DqaInvalidCategoryoptionRemarks"),
                    _item("Check measures", "data_quality.DqaInvalidMeasuretypeRemarks"),
                    _item("Check periods", "data_quality.DqaInvalidPeriodRemarks"),
                    _item("Check sources", "data_quality.DqaInvalidDatasourceRemarks"),
                    _item("External consistencies", "data_quality.DqaExternalConsistencyOutliersRemarks"),
                    _item("Internal consistencies", "data_quality.DqaInternalConsistencyOutliersRemarks"),
                    _item("Missing values", "data_quality.MissingValuesRemarks"),
                    _item("Similarity scores", "data_quality.Similarity_Index"),
                    _item("Multiple measures", "data_quality.Mutiple_MeasureTypes"),
                    _item("Value type checks", "data_quality.DqaValueTypesConsistencyRemarks"),
                ],
            }
        ],
    },
    {
        "label": "API tokens",
        "icon": "api",
        "groups": [
            {
                "label": "API tokens",
                "items": [_item("Token status", url_name="aho_api_token_status")],
            }
        ],
    },
    {
        "label": "Authentication",
        "icon": "auth",
        "groups": [
            {
                "label": "Authentication",
                "items": [
                    _item("Users", "authentication.CustomUser"),
                    _item("Roles", "authentication.CustomGroup"),
                    _item("Permissions"),
                    _item("User history", "authentication.AhodctUserLogs"),
                ],
            }
        ],
    },
]


@dataclass(frozen=True)
class ModelRef:
    app_label: str
    model_name: str

    @classmethod
    def from_string(cls, value: str) -> "ModelRef":
        app_label, model_name = value.split(".", 1)
        return cls(app_label, model_name)


def _admin_url(model_ref: str | None, url_name: str | None = None) -> str | None:
    if url_name:
        try:
            return reverse(url_name)
        except NoReverseMatch:
            return None

    if not model_ref:
        return None

    ref = ModelRef.from_string(model_ref)
    try:
        model = apps.get_model(ref.app_label, ref.model_name)
    except LookupError:
        return None

    if model not in admin.site._registry:
        return None

    try:
        return reverse(f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist")
    except NoReverseMatch:
        return None


@register.simple_tag(takes_context=True)
def aho_laravel_menu(context: dict[str, Any]) -> list[dict[str, Any]]:
    request = context.get("request")
    current_path = getattr(request, "path", "")
    menu: list[dict[str, Any]] = [
        {
            "label": _ui_label("Dashboard"),
            "icon": "dashboard",
            "url": reverse("admin:index"),
            "active": current_path.rstrip("/") == reverse("admin:index").rstrip("/"),
            "groups": [],
        }
    ]

    for section in LARAVEL_MENU:
        rendered_groups = []
        active_section = False
        first_url = None

        for group in section["groups"]:
            rendered_items = []
            for item in group["items"]:
                url = _admin_url(item.get("model"), item.get("url_name"))
                if first_url is None and url:
                    first_url = url
                active = bool(url and current_path.startswith(url))
                active_section = active_section or active
                rendered_items.append(
                    {
                        "label": _ui_label(item["label"]),
                        "url": url,
                        "active": active,
                        "disabled": url is None,
                    }
                )

            rendered_groups.append({"label": _ui_label(group["label"]), "items": rendered_items})

        menu.append(
            {
                "label": _ui_label(section["label"]),
                "icon": section.get("icon", "default"),
                "url": first_url,
                "groups": rendered_groups,
                "active": active_section,
            }
        )

    return menu


@register.simple_tag(takes_context=True)
def aho_breadcrumb_trail(context: dict[str, Any], title: str = "") -> list[dict[str, str | None]]:
    """Build the page path from the Laravel-like menu shown in the sidebar."""
    try:
        home_url = reverse("admin:index")
    except NoReverseMatch:
        home_url = None

    crumbs: list[dict[str, str | None]] = [{"label": _ui_label("Home"), "url": home_url}]

    for section in aho_laravel_menu(context):
        if not section.get("active") or not section.get("groups"):
            continue

        crumbs.append({"label": section["label"], "url": section.get("url")})
        for group in section.get("groups", []):
            active_item = next((item for item in group.get("items", []) if item.get("active")), None)
            if not active_item:
                continue
            if group.get("label"):
                crumbs.append({"label": group["label"], "url": None})
            crumbs.append({"label": active_item["label"], "url": active_item.get("url")})
            return crumbs
        return crumbs

    title_text = str(title or "").strip()
    if title_text and title_text != crumbs[-1]["label"]:
        crumbs.append({"label": title_text, "url": None})
    return crumbs


@register.simple_tag(takes_context=True)
def aho_search_index(context: dict[str, Any]) -> list[dict[str, str]]:
    """Flatten the Laravel-like navigation into a topbar search index."""
    entries: list[dict[str, str]] = []
    for section in aho_laravel_menu(context):
        if section.get("url"):
            entries.append(
                {
                    "label": section["label"],
                    "section": section["label"],
                    "group": "",
                    "url": section["url"],
                }
            )
        for group in section.get("groups", []):
            for item in group.get("items", []):
                if item.get("disabled") or not item.get("url"):
                    continue
                entries.append(
                    {
                        "label": item["label"],
                        "section": section["label"],
                        "group": group.get("label", ""),
                        "url": item["url"],
                    }
                )
    return entries


@register.simple_tag(takes_context=True)
def aho_active_submenu(context) -> dict[str, Any] | None:
    """Return the active Laravel-like section so the template can render one submenu rail."""
    for section in aho_laravel_menu(context):
        if section.get("active") and section.get("groups"):
            return section
    return None


def _model(path: str):
    try:
        app_label, model_name = path.split(".", 1)
        return apps.get_model(app_label, model_name)
    except LookupError:
        return None


INDICATOR_DATA_MODEL_PATHS = (
    "indicators.FactDataIndicator",
    "indicators.aho_factsindicator_archive",
)
DASHBOARD_CACHE_SECONDS = 300


def _indicator_data_models() -> list[Any]:
    models = []
    for path in INDICATOR_DATA_MODEL_PATHS:
        model = _model(path)
        if model is not None:
            models.append(model)
    return models


def _count(path: str, filters: dict[str, Any] | None = None) -> int:
    model = _model(path)
    if model is None:
        return 0

    try:
        qs = model.objects.all()
        if filters:
            qs = qs.filter(**filters)
        return qs.count()
    except Exception:
        return 0


def _count_indicator_data(filters: dict[str, Any] | None = None) -> int:
    return sum(_count(path, filters) for path in INDICATOR_DATA_MODEL_PATHS)


def _indicator_data_status_summary(model_paths: tuple[str, ...] | None = None) -> dict[str, int]:
    summary = {"total": 0, "approved": 0, "pending": 0, "rejected": 0}
    models = [_model(path) for path in (model_paths or INDICATOR_DATA_MODEL_PATHS)]
    for model in models:
        if model is None:
            continue
        try:
            rows = model.objects.order_by().values("comment").annotate(total=Count("fact_id"))
            for row in rows:
                total = row["total"]
                status = (row.get("comment") or "").strip().lower()
                summary["total"] += total
                if status in summary:
                    summary[status] += total
        except Exception:
            continue
    return summary


def _distinct(path: str, field: str) -> int:
    model = _model(path)
    if model is None:
        return 0

    try:
        return model.objects.order_by().exclude(**{f"{field}__isnull": True}).values(field).distinct().count()
    except Exception:
        return 0


def _distinct_indicator_data(field: str) -> int:
    values = set()
    for model in _indicator_data_models():
        try:
            values.update(
                value
                for value in model.objects.order_by().exclude(**{f"{field}__isnull": True})
                .values_list(field, flat=True)
                .distinct()
                if value is not None
            )
        except Exception:
            continue
    return len(values)


def _label(value: Any) -> str:
    try:
        text = str(value)
    except Exception:
        text = ""
    return text.strip() or "Not available"


def _with_bars(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    numeric_values = [row.get("value", 0) for row in rows if isinstance(row.get("value"), (int, float))]
    max_value = max(numeric_values) if numeric_values else 0
    for index, row in enumerate(rows):
        if isinstance(row.get("value"), (int, float)) and max_value:
            row["bar"] = max(6, round((row["value"] / max_value) * 100, 2))
        else:
            row["bar"] = max(20, 100 - (index * 15))
    return rows


def _recent_uploads(limit: int = 5) -> list[dict[str, Any]]:
    rows = []
    for path, source_label in (
        ("indicators.FactDataIndicator", "Fact indicator data"),
        ("indicators.aho_factsindicator_archive", "Archive"),
    ):
        model = _model(path)
        if model is None:
            continue
        try:
            queryset = model.objects.select_related("indicator").order_by("-fact_id")[: limit * 3]
            for row in queryset:
                timestamp = getattr(row, "date_created", None) or getattr(row, "date_lastupdated", None)
                try:
                    sort_value = timestamp.timestamp() if timestamp else 0
                except Exception:
                    sort_value = 0
                rows.append({"row": row, "source": _ui_label(source_label), "sort": sort_value})
        except Exception:
            continue

    rows.sort(key=lambda item: item["sort"], reverse=True)
    data = []
    for index, item in enumerate(rows[:limit]):
        row = item["row"]
        period = getattr(row, "end_period", "") or getattr(row, "period", "")
        meta = str(period) if period else item["source"]
        if period:
            meta = f"{meta} - {item['source']}"
        data.append(
            {
                "label": _label(getattr(row, "indicator", "")),
                "meta": meta,
                "value": period or index + 1,
                "bar": max(20, 100 - (index * 14)),
            }
        )
    return data


def _related_label(field: str, key: Any) -> str:
    for model in _indicator_data_models():
        try:
            relation = model._meta.get_field(field)
            related_model = relation.remote_field.model
            return _label(related_model.objects.get(pk=key))
        except Exception:
            continue
    return f"#{key}"


def _top_indicator_data_values(field: str, limit: int = 5) -> list[dict[str, Any]]:
    totals: Counter[Any] = Counter()
    for model in _indicator_data_models():
        try:
            rows = (
                model.objects.order_by()
                .exclude(**{f"{field}__isnull": True})
                .values(field)
                .annotate(total=Count(field))
            )
            for row in rows:
                key = row.get(field)
                if key is not None:
                    totals[key] += row["total"]
        except Exception:
            continue

    data = [
        {
            "label": _related_label(field, key),
            "value": total,
            "meta": _ui_label("Active + archived records"),
        }
        for key, total in totals.most_common(limit)
    ]
    return _with_bars(data)


def _top_values(path: str, field: str, label_field: str, limit: int = 5) -> list[dict[str, Any]]:
    model = _model(path)
    if model is None:
        return []

    try:
        rows = (
            model.objects.order_by()
            .values(field, label_field)
            .annotate(total=Count(field))
            .order_by("-total")[:limit]
        )
        return _with_bars([
            {"label": row.get(label_field) or f"#{row.get(field)}", "value": row["total"], "meta": "records"}
            for row in rows
        ])
    except Exception:
        return []


def _period_values(limit: int = 5) -> list[dict[str, Any]]:
    totals: Counter[str] = Counter()
    for model in _indicator_data_models():
        try:
            rows = model.objects.order_by().values("end_period").annotate(total=Count("fact_id"))
            for row in rows:
                label = str(row.get("end_period") or _label(""))
                totals[label] += row["total"]
        except Exception:
            continue

    def sort_key(item: tuple[str, int]) -> tuple[int, str]:
        try:
            return (int(item[0]), item[0])
        except Exception:
            return (-1, item[0])

    rows = sorted(totals.items(), key=sort_key, reverse=True)[:limit]
    return _with_bars(
        [
            {
                "label": period,
                "value": total,
                "meta": _ui_label("Active + archived records"),
            }
            for period, total in rows
        ]
    )


@register.simple_tag
def aho_dashboard() -> dict[str, Any]:
    language = translation.get_language() or "en"
    cache_key = f"aho-dashboard:v5:{language}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    locations = _count("regions.StgLocation")
    level2_locations = _count("regions.StgLocation", {"locationlevel_id": 2})
    status_summary = _indicator_data_status_summary(("indicators.FactDataIndicator",))
    indicator_values = status_summary["total"]

    dashboard = {
        "cards": [
            {
                "label": _ui_label("Locations"),
                "value": locations,
                "description": _ui_label("Level 2 locations: {count}").format(count=level2_locations),
            },
            {
                "label": _ui_label("Indicators"),
                "value": _count("indicators.StgIndicator"),
                "description": _ui_label("Indicators with values: {count}").format(
                    count=_distinct_indicator_data("indicator")
                ),
            },
            {
                "label": _ui_label("Values"),
                "value": indicator_values,
                "description": _ui_label("Approved: {approved} | Pending: {pending} | Rejected: {rejected}").format(
                    approved=status_summary["approved"],
                    pending=status_summary["pending"],
                    rejected=status_summary["rejected"],
                ),
            },
            {
                "label": _ui_label("Archive"),
                "value": _count("indicators.aho_factsindicator_archive"),
                "description": _ui_label("Values from fact_data_archive"),
            },
            {
                "label": _ui_label("Sources / methods / categories"),
                "value": f"{_count('home.StgDatasource')} / {_count('home.StgMeasuremethod')} / {_count('home.StgCategoryoption')}",
                "description": _ui_label("Data sources / measure methods / categories"),
            },
            {
                "label": _ui_label("Users"),
                "value": _count("authentication.CustomUser"),
                "description": _ui_label("Registered application accounts"),
            },
        ],
        "charts": [
            {
                "title": _ui_label("Top 5 recently loaded indicators"),
                "rows": _recent_uploads(),
            },
            {
                "title": _ui_label("Top 5 indicators used for the African Region"),
                "rows": _top_indicator_data_values("indicator"),
            },
            {
                "title": _ui_label("Top 5 indicators loaded by countries"),
                "rows": _top_indicator_data_values("location"),
            },
            {
                "title": _ui_label("Top 5 data sources used"),
                "rows": _top_indicator_data_values("datasource"),
            },
        ],
        "language": language,
    }
    cache.set(cache_key, dashboard, DASHBOARD_CACHE_SECONDS)
    return dashboard


@register.simple_tag
def aho_topbar_alerts() -> dict[str, Any]:
    """Return topbar messages and action-required notifications like Laravel."""
    recent_since = timezone.now() - timedelta(days=7)
    message_url = _admin_url("authentication.AhodctUserLogs")
    notification_items = _pending_notification_items()
    notification_count = sum(item["count"] for item in notification_items)
    message_items = _latest_activity_messages(message_url)
    message_count = LogEntry.objects.filter(action_time__gte=recent_since).count()

    return {
        "messages": {
            "count": message_count,
            "label": _ui_label("Messages"),
            "title": _ui_label("Received messages"),
            "summary": _summary_text(message_count, "messages"),
            "empty": _ui_label("No recent messages"),
            "url": message_url,
            "items": message_items,
        },
        "notifications": {
            "count": notification_count,
            "label": _ui_label("Notifications"),
            "title": _ui_label("System notifications"),
            "summary": _summary_text(notification_count, "pending"),
            "empty": _ui_label("No pending notifications"),
            "url": notification_items[0]["url"] if notification_items else _admin_url("indicators.FactDataIndicator"),
            "items": notification_items[:5],
        },
    }


def _summary_text(count: int, kind: str) -> str:
    if kind == "pending":
        if count == 0:
            return _ui_label("No pending items")
        return f"{count} {_ui_label('pending item' if count == 1 else 'pending items')}"
    if count == 0:
        return _ui_label("No new messages")
    return f"{count} {_ui_label('new message' if count == 1 else 'new messages')}"


def _latest_activity_messages(fallback_url: str | None) -> list[dict[str, str]]:
    action_labels = {
        1: _ui_label("Created"),
        2: _ui_label("Changed"),
        3: _ui_label("Deleted"),
    }
    items: list[dict[str, str]] = []
    for entry in LogEntry.objects.select_related("content_type", "user").order_by("-action_time")[:5]:
        model_label = entry.content_type.name.title() if entry.content_type else _ui_label("Messages")
        actor = entry.user.get_username() if entry.user_id else ""
        body_parts = [entry.object_repr or model_label]
        if actor:
            body_parts.append(actor)
        items.append(
            {
                "title": f"{action_labels.get(entry.action_flag, _ui_label('Messages'))}: {model_label}",
                "body": " - ".join(body_parts),
                "when": timezone.localtime(entry.action_time).strftime("%Y-%m-%d %H:%M"),
                "url": fallback_url or "#",
            }
        )
    return items


def _pending_notification_items() -> list[dict[str, Any]]:
    targets = [
        ("indicators.FactDataIndicator", "comment", _ui_label("Indicator values")),
        ("publications.StgKnowledgeProduct", "comment", _ui_label("Knowledge products")),
    ]
    items: list[dict[str, Any]] = []
    for model_path, status_field, label in targets:
        model = _model(model_path)
        if model is None:
            continue
        try:
            model._meta.get_field(status_field)
        except Exception:
            continue
        try:
            queryset = model.objects.filter(**{f"{status_field}__iexact": "pending"})
            count = queryset.count()
        except Exception:
            continue
        if not count:
            continue
        latest = None
        try:
            latest = queryset.order_by("-date_lastupdated", "-date_created").first()
        except Exception:
            latest = queryset.first()
        items.append(
            {
                "title": f"{label}: {count}",
                "body": _ui_label("Pending approval"),
                "when": _record_time(latest),
                "url": _status_filtered_admin_url(model_path, status_field, "pending") or "#",
                "count": count,
            }
        )
    return items


def _status_filtered_admin_url(model_path: str, status_field: str, status: str) -> str | None:
    base_url = _admin_url(model_path)
    if not base_url:
        return None
    return f"{base_url}?{urlencode({f'{status_field}__exact': status})}"


def _record_time(record: Any) -> str:
    if record is None:
        return ""
    value = getattr(record, "date_lastupdated", None) or getattr(record, "date_created", None)
    if not value:
        return ""
    try:
        return timezone.localtime(value).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(value)
