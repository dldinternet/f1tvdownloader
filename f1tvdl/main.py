import os, sys, re
import logging
from tf import trap_import_error, __version__
from tf import __whl__, LE_TF_DEVELOP, __pkg_path__, __mod_rel_path__, __pkg__

try:
  import click
  from click import get_current_context
  import pyfiglet

  # noinspection PyUnresolvedReferences
  from windsor.utils import askString, AWSProfileValidator, FaroProfileValidator, FilePathValidator
  from tf.cli import TDCCLI
  from tf.clicontext import pass_context
except ImportError as ie:
  trap_import_error(ie)
except Exception:
  raise

CONTEXT_SETTINGS = dict(auto_envvar_prefix='LE_TF')
LOG_LEVEL_CHOICES = [level for level in list(logging._nameToLevel.keys()) if isinstance(level, str)]


def show_version(ctx, param, value):
  if value and not ctx.resilient_parsing:
    # pyfiglet.print_figlet(__pkg__.upper())
    print(__pkg__.upper()+' CLI v'+__version__)
    ctx.exit()


@click.command(cls=TDCCLI, context_settings=CONTEXT_SETTINGS)
@click.option('--aws_profile',
              '--awsprofile',
              '--aws-profile',               type=click.types.StringParamType(),                                           help='AWS profile')
@click.option('--faro-profile',
              '--faro_profile',
              '--profile', 					        type=click.types.StringParamType(),                                           help='Faro profile')
@click.option('--profile-region', 			    type=click.types.StringParamType(),                 default='us-east-1',      help='Faro profile region')
@click.option('--region', 					        type=click.types.StringParamType(),                 default='us-east-1',      help='Region')
@click.option('--format', 					        type=click.types.Choice(['text', 'json', 'csv']),   default='text',           help='Output format')
@click.option('--family', 					        type=click.types.StringParamType(),                 required=False,           help='Family Id')
@click.option('--workflow', 				        type=click.types.StringParamType(),                 required=False,           help='Workflow Id')
@click.option('--sts-profile',
              '--sts_profile', 	    type=click.types.StringParamType(),                 required=False,           help='Deployment STS profile. Use this to analyze deployments NOT in the same account as the Faro or AWS profiles')
@click.option('-M',
              '--profile-account-map',
              '--profile_account_map',      type=click.types.StringParamType(),                                           help='STS profile to AWS Account mappings')
@click.option('-v',
              '--verbose/--no-verbose', 	  is_flag=True,                                       default=False, 						help='Enables verbose mode.')
@click.option('-d',
              '--debug/--no-debug', 		    is_flag=True,                                       default=False, 						help='Enables debug mode.')
@click.option('-t',
              '--trace/--no-trace', 		    is_flag=True,                                       default=False, 						help='Enables trace mode.')
@click.option('--log-file',
              '--log_file', 		            type=click.types.StringParamType(),                 default=None,             help='Log file path. Default: None')
@click.option('--log-level',
              '--log_level', 	              type=click.types.Choice(LOG_LEVEL_CHOICES),         default='WARN',           help='Log file path. Default: None')
@click.option('--color/--no-color', 		    is_flag=True,                                       default=True, 						help='Use colored output')
@click.option('--prompt', 		              is_flag=True,                                       default=False, 						help='Prompt for Faro or AWS profile name')
@click.option('--local-output',
              '--local_output',
              '--output', 				          type=click.types.StringParamType(),                 required=False,           help='Output location for deckspec and parameters. Default: local', default='local')
@click.option('--ap',
              '--infrastructure-code-path',
              '--iac_path',          type=click.types.StringParamType(),                        required=False,           help='Infrastructure code files location. Default: farosrc/tam', default='farosrc/tam')
@click.option('--show-version',
              '--version',
              '--show_version',             is_flag=True,                                       default=False, 						help='Show version', callback=show_version)
@pass_context
def main(ctx, **kwargs):
    """TAM deploy CloudFront automation CLI"""
    if kwargs['format'] == 'text':
        pyfiglet.print_figlet(__pkg__.upper()+' CLI')

    ctx.set_params(**kwargs)

    family = getattr(ctx, 'family', None)
    workflow = getattr(ctx, 'workflow', None)
    # if not (family) or (workflow and not family):
    #   ctx.elog('--family (with --workflow) must be provided or alternatively --deployment or --stack)')
    #   # sys.exit(1)

    ctx.families = getattr(ctx, 'families', re.split(',+\s*', family) if family else [])
    ctx.workflows = getattr(ctx, 'workflows', re.split(',+\s*', workflow) if workflow else [])
    ctx.deployments = [] # getattr(ctx, 'deployments', re.split(',+\s*', deployment) if deployment else [])
    if ctx.sts_profile is None:
      ctx.sts_profile = ctx.aws_profile

    # ctx.profile_account_map =
    ctx.json_file_or_string('profile_account_map')
    ctx.json_or_csv_file_or_string('acm_lambda_deployments', default='[]')
    ctx.json_or_csv_file_or_string('acm_lambda_decks', default='[]')
    ctx.json_or_csv_file_or_string('acm_lambda_groups', default='[]')

    if getattr(ctx, 'profile', None) == 'default' and getattr(ctx, 'aws_profile', None) is None:
        ctx.vlog('WARNING: default Faro profile used.')


if __name__ == '__main__':
    import re
    import sys
    from pkg_resources import load_entry_point

    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.argv[0] = re.sub(r'__main__(\.py)?$', __whl__, sys.argv[0])
    sys.exit(load_entry_point('tdc', 'console_scripts', 'tdc')())
