from cli.cli import CLIObject
import click

@click.group()
@click.option('--test/--dont_test', default=False, help="Uses test information")
@click.option('--template', type=click.STRING, default=None, help="Define the template")
@click.option('--read/--dontread', is_flag=True, default=False, help="Readin pickled data")
@click.option('--write/--dontwrite', is_flag=True, default=True, help="Write pickled data")
@click.pass_context
def synctree_entry(ctx, test, template, read, write):
    """ entry point """
    ctx.obj = CLIObject(test)
    ctx.obj.template = template

    if ctx.obj.test or template is None:
        pass #template = "dss.templates.DefaultTemplate"
    else:
        pass #template = "ssis_dss.templates.templates.{}".format(template)

    ctx.obj.init_synctreetest(template, read, write)

@synctree_entry.command('test')
@click.pass_obj
def synctree_test(obj):
    import pytest
    pytest.main()

