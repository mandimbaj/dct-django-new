from import_export import resources
from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget
from .models import (StgProductDomain,StgKnowledgeProduct,StgResourceType,
    StgResourceCategory,)
from home.models import StgDatasource
from regions.models import StgLocation

# Davy's Skype 26/10/2018 suggestions - limit fields to be imported/exported
# using ModelResource. This also applies to
class StgKnowledgeProductResourceExport (resources.ModelResource):
    title = Field(attribute='title', column_name='Resource Name')
    code = Field(attribute='code', column_name='Resource Code')
    resource_type = Field(attribute='type', column_name='Resource Type')
    categorization = Field(attribute='categorization',
        column_name='Reseource Categorization',)
    location = Field(attribute='location__name', column_name='Location Name')
    author = Field(attribute='author', column_name='Author')
    year_published = Field(attribute='year_published',column_name='Year Published')
    external_url = Field(attribute='external_url', column_name='Hyperlink (URL)')


    class Meta:
        model = StgKnowledgeProduct
        skip_unchanged = False
        report_skipped = False
        fields=('code','title','resource_type','categorization','location',
            'author','year_published','external_url',)


class StgKnowledgeProductResourceImport (resources.ModelResource):
    def before_save_instance(
        self, instance, using_transactions, dry_run):
        save_instance( # Called with dry_run=True to ensure no records are saved
            instance, using_transactions=True, dry_run=True)

    def get_instance(self, instance_loader, row):
        return False  # To override the need for the id in the import file

    def save_instance(self, instance, using_transactions=True, dry_run=False):
        if dry_run:
            pass
        else:
            instance.save()

    code = Field( column_name='Resource Code', attribute='code',)
    title = Field(column_name='Title', attribute='title')
    type = Field(column_name='Reseource Type', attribute='type')
    categorization = Field(column_name='Reseource Categorization',
        attribute='categorization')
    location_code = Field(column_name='Location Code',attribute='location_code',
        widget=ForeignKeyWidget(StgLocation, 'code'))
    location_name = Field( # Define the location name but exclude it in processing the file
        column_name='Location Name',
        attribute='location',
        widget=ForeignKeyWidget(StgLocation, 'name'))
    repository = Field(
        column_name=' Reference Name',
        attribute='repository',
        widget=ForeignKeyWidget(StgDatasource, 'code'))
    description = Field(
        column_name='Description', attribute='description')
    abstract = Field(column_name='Abstract', attribute='abstract')
    author = Field(column_name='Author(s)', attribute='author')
    year_published = Field(column_name='Year', attribute='year_published')
    external_url = Field(column_name='External Link', attribute='external_url')

    class Meta:
        model = StgKnowledgeProduct
        skip_unchanged = False
        report_skipped = False
        fields = ('code','title', 'type','categorization','location_code',
            'location_name','repository','description','abstract', 'author',
            'year_published','external_url', )


class ProductDomainResourceExport(resources.ModelResource):
    domain_name = Field(attribute='name', column_name='Theme/Domain Name')
    domain_code= Field(attribute='code', column_name='Theme Code')
    shortname = Field(attribute='shortname', column_name='Short Name')
    description = Field(attribute='description', column_name='Description')
    parent = Field(attribute='parent', column_name='Parent')
    level = Field(attribute='level', column_name='Level')

    class Meta:
        model = StgProductDomain
        skip_unchanged = False
        report_skipped = False
        fields = ('domain_name','domain_code','shortname', 'description',
            'parent','level',)


class ProductTypeResourceExport(resources.ModelResource):
    name = Field(attribute='name', column_name='Product Type')
    code= Field(attribute='code', column_name='Code')
    shortname = Field(attribute='shortname', column_name='Short Name')
    description = Field(attribute='description', column_name='Description')

    class Meta:
        model = StgResourceType
        skip_unchanged = False
        report_skipped = False
        fields = ('name','code','shortname', 'description',)

class ProductCategoryResourceExport(resources.ModelResource):
    name = Field(attribute='name', column_name='Product Category')
    code= Field(attribute='code', column_name='Code')
    shortname = Field(attribute='shortname', column_name='Short Name')
    description = Field(attribute='description', column_name='Description')

    class Meta:
        model = StgResourceCategory
        skip_unchanged = False
        report_skipped = False
        fields = ('name','code','shortname','description',)
