import datetime
import json
import os
import re
from json import JSONDecodeError

import sys

import six
import time

import pyconfigstore
import windsor.logging
import click.decorators
from click import get_current_context
from windsor.clicontext import WindsorCLIContext

import tf
import yaml

from windsor.utils import instance_cache, askString, FaroProfileValidator, AWSProfileValidator

from tf.errors import TDCError
from tf.tdchelper import TdcHelper
from faro.errors import FaroClientError
from jinja2 import Environment, PackageLoader
from faro.FaroLibrary import FaroLibrary

class TDCCLIContext(WindsorCLIContext, TdcHelper):

    FARO_DECK_TEMPLATE='emulated.deckspec.jinja2'
    FARO_PARAM_TEMPLATE='emulated.parameters.yaml.jinja2'
    # USE_WINDSOR_WEBSERVICE_CLIENT = False
    USE_FARO_WEBSERVICE_CLIENT = True

    def __init__(self):
        self._conf = getattr(self, '_conf', pyconfigstore.ConfigStore(tf.__pkg__.upper()))
        super(TDCCLIContext, self).__init__()
        self.commands_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'commands'))

    def __getattr__(self, item):
        raise AttributeError(item)

    @instance_cache
    def file_or_string(self, attribute, default=''):
        string = getattr(self, attribute, default) or default
        if string == default:
            setattr(self, attribute, string)
        if string:
            try:
                file = os.path.expanduser(string)
                if os.path.isfile(file):
                    with open(file, 'r') as fp:
                        return fp.read()
                else:
                    raise TypeError('--{} is not a file'.format(attribute))
            except TypeError:  # Not a file so assume string
                pass
        return string
        # assert False

    @instance_cache
    def json_file_or_string(self, attribute, default='{}'):
        try:
            setattr(self, attribute, json.loads(self.file_or_string(attribute, default=default)))
            return getattr(self, attribute)
        except (TypeError, JSONDecodeError) as jde:
            raise TDCError('--{} is not valid JSON!?: "{}" ({})'.format(attribute, getattr(self, attribute), ';'.join(jde.args)))

    @instance_cache
    def json_or_csv_file_or_string(self, attribute, default='{}'):
        initial = getattr(self, attribute, None)
        try:
            setattr(self, attribute, json.loads(self.file_or_string(attribute, default=default)))
        except (TypeError, JSONDecodeError) as jde:
            setattr(self, attribute, initial)
            string = self.file_or_string(attribute=attribute, default='')
            setattr(self, attribute, re.split(',\s*', getattr(self, attribute)))
        return getattr(self, attribute)

    @instance_cache
    def jsonify(self, *args, **kwargs):
        return self.windsor().jsonify(*args, **kwargs)

    def set_params(self, load_config=False, **kwargs):
        super(TDCCLIContext, self).set_params(load_config=load_config, **kwargs)

    @instance_cache
    def get_deployment_name(self):
        return '%s-emulated' % self.stack

    def check_params(self, *args, **kwargs):
        if not getattr(self, 'stack', None):
            self.elog('--stack must be provided)')
            sys.exit(1)
        if getattr(self, 'output', '-None-') is '-None-':
            self.output = getattr(self, 'local_output', None)
        if not getattr(self, 'deployment', None):
            self.deployment = self.get_deployment_name()
        if not getattr(self, 'deckspec', None):
            self.deckspec = os.path.join(self.output, '{}.deckspec'.format(self.deployment))
        if not getattr(self, 'parameters_file', None):
            self.parameters_file = os.path.join(self.output, '{}-emulated.parameters.yaml'.format(self.stack))

    def determine_profile(self, **kwargs):
        # Here we try to sort out all the aliases for ctx.aws_profile
        # If --aws_profile was NOT given we stake our claim ...
        if getattr(self, 'aws_profile', None) is None:
            self.aws_profile = kwargs.get('aws_profile', kwargs.get('awsprofile', os.environ.get('AWS_PROFILE', None)))
        # # let's see if we have a parameter by the alternate name
        # elif kwargs.get('awsprofile', None):
        #     self.aws_profile = kwargs['awsprofile']
        # elif os.environ.get('AWS_PROFILE', None):
        #     self.aws_profile = os.environ['AWS_PROFILE']
        # but Click may want to call it aws_profile (same for aws-profile alias luckily)
        try: del kwargs['awsprofile']
        except: pass
        if getattr(self, 'profile', None) is None:
            self.profile = kwargs.get('profile', getattr(self, 'aws_profile', os.environ.get('AWS_PROFILE', None)))
        # If neither parameter given
        if self.profile is None and self.aws_profile is None and self.prompt:
            self.profile = askString(
                message='Enter the Faro profile name (Enter "skip" to skip over this entry and use AWS profile instead)',
                validator=FaroProfileValidator)
            if self.profile == 'skip' or self.profile == '':
                self.profile = None
        if self.profile is None and self.aws_profile is None:
            if self.prompt:
                self.aws_profile = askString(message='Enter the AWS profile name', validator=AWSProfileValidator)
            else:
                self.elog('One of --aws_profile or --profile is required')
                print(get_current_context().get_help())
                exit(1)

    def _srcfile(self, skip=0):
        f = windsor.logging.currentframe(skip=skip+1)
        if hasattr(f, "f_code"):
            co = f.f_code
            filename = os.path.normcase(co.co_filename)
            return filename
        return __file__

    def clog(self, msg, *args, **kwargs):
        kwargs['package_name'] = kwargs.get('package_name', tf.PACKAGE_NAME)
        kwargs['srcfile']      = kwargs.get('srcfile', self._srcfile(skip=1))
        kwargs['skip']         = kwargs.get('skip', 1)
        super(TDCCLIContext, self).clog(msg, *args, **kwargs)

    def elog(self, msg, *args, **kwargs):
        kwargs['package_name'] = kwargs.get('package_name', tf.PACKAGE_NAME)
        kwargs['srcfile']      = kwargs.get('srcfile', self._srcfile(skip=1))
        kwargs['skip']         = kwargs.get('skip', 1)
        super(TDCCLIContext, self).elog(msg, *args, **kwargs)

    def wlog(self, msg, *args, **kwargs):
        kwargs['package_name'] = kwargs.get('package_name', tf.PACKAGE_NAME)
        kwargs['srcfile']      = kwargs.get('srcfile', self._srcfile(skip=1))
        kwargs['skip']         = kwargs.get('skip', 1)
        super(TDCCLIContext, self).wlog(msg, *args, **kwargs)

    def vlog(self, msg, *args, **kwargs):
        kwargs['package_name'] = kwargs.get('package_name', tf.PACKAGE_NAME)
        kwargs['srcfile']      = kwargs.get('srcfile', self._srcfile(skip=1))
        kwargs['skip']         = kwargs.get('skip', 1)
        super(TDCCLIContext, self).vlog(msg, *args, **kwargs)

    def dlog(self, msg, *args, **kwargs):
        kwargs['package_name'] = kwargs.get('package_name', tf.PACKAGE_NAME)
        kwargs['srcfile']      = kwargs.get('srcfile', self._srcfile(skip=1))
        kwargs['skip']         = kwargs.get('skip', 1)
        super(TDCCLIContext, self).dlog(msg, *args, **kwargs)

    def check_deployment(self, deployment=None, first=True):
        try:
            if not deployment:
                deployment = self.deployment
            deployment_details = self.get_deployment_fresh(Name=deployment, Region=self.region, Profile=None, AwsProfile=self.sts_profile, Format='raw')
            msg = "Deployment '{}' exists.".format(deployment)
            if self._trace:
                if first:
                    self.wlog(msg)
                else:
                    print(msg)
            else:
                print(msg)
            if not self.update and first:
                self.elog(
                    "Use --update argument to update the deployment or use Faro CLI to delete the deployment and start over.\n(In the future we will provide a way to delete the deployment here)")
                exit(1)
            return True
        except FaroClientError as fce:
            if getattr(self, 'update', False):
                self.wlog("Deployment '{}' does not exist.".format(deployment))
                self.wlog("Use --update argument only to update an existing deployment -- ignoring --update")
                self.update = False
            msg = "Deployment '{}' does not exist.".format(deployment)
            if self._trace:
                self.wlog(msg)
            else:
                print(msg)
            if getattr(fce, 'response', None):
                if fce.response.get('message', None):
                    self.elog(fce.response['message'])
            try:
                if fce.error.response.status_code != 404:
                    raise fce
                else:
                    self.dlog('Faro API returned 404 on get_deployment({})'.format(deployment))
                    return False
            except:
                raise fce


    def save_parameters(self):
        path = os.path.dirname(self.parameters_file)
        if not os.path.exists(path):
            msg = 'Cannot save parameters to "{}". Directory "{}" does not exists or is not accessible.'.format(self.parameters_file, path)
            self.elog(msg)
            exit(1)
        with open(self.parameters_file, 'w+') as fh:
            yaml.dump(data=self.parameters, default_flow_style=False, stream=fh)
            fh.close()

    def parse_parameters_string(self, parameterstring=None):
        if not parameterstring and getattr(self, 'parameters', None) and isinstance(self.parameters, str):
            parameterstring = self.parameters
        if isinstance(parameterstring, six.string_types):
            parameters = {}
            for param in re.split(',\s*', parameterstring):
                k, v = re.split('=', param)
                parameters[k] = v
            # self.parameters = parameters
            return parameters
        else:
            return parameterstring

    def update_parameters(self):
        if os.path.exists(self.parameters_file):
            parameters = self.parse_parameters_string()
            with open(self.parameters_file) as fh:
                self.parameters = yaml.safe_load(fh)
                fh.close()
            if isinstance(parameters, (dict)):
                self.parameters.update(parameters)
            return True
        return False

    def update_parameters_file(self):
        if not os.path.exists(self.parameters_file) or self.update_parameters():
            self.save_parameters()
            return True
        return False

    def monitor_progress(self, deck, deployment):

        time.sleep(5)
        while True:
            # Get deployment status
            try:
                deployment_details = self.get_deployment_fresh(Name=deployment, Region=self.region, Profile=None, AwsProfile=self.sts_profile, Format='raw')
                if self._verbose:
                    self.vlog('{} State == {}'.format(datetime.datetime.now().strftime('%Y-%m-%d:%H:%M:%S'), deployment_details['State']))
                else:
                    sys.stdout.write('.')
                if re.search('(FAILED|COMPLETE)$', deployment_details['State']):
                    sys.stdout.write("\n    ")
                    break
                time.sleep(5)
            except FaroClientError as fce:
                try:
                    if fce.error.response.status_code != 404:
                        raise fce
                except:
                    raise fce


    def deploy_emulated_decks(self):
        result = self.cloudformation_describe_stacks(profile_name=self.aws_profile, region_name=self.region,
                                                     api_args={'StackName': self.stack}, cache_buster=datetime.datetime.now())
        for stack in result:
            haystack = {'deckspec': self.FARO_DECK_TEMPLATE, 'parameters_file': self.FARO_PARAM_TEMPLATE}
            expanded = {}
            for attr, jinja2file in haystack.items():
                f = sys._getframe(0)
                jinja = Environment(loader=PackageLoader(f.f_globals['__package__'], 'templates')).get_template(jinja2file)
                # ctx.dlog(ctx.format_result(stack, indent=2))
                template = self.cloudformation_get_template(profile_name=self.aws_profile, region_name=self.region,
                                                            api_args={'StackName': self.stack, 'TemplateStage': 'Processed'})
                for param, value in template['TemplateBody']['Parameters'].items():
                    if not value.get('Description', None) or value['Description'] == '':
                        value['Description'] = param

                parameter_keys = [param for param in template['TemplateBody']['Parameters']]
                output_keys = [output['OutputKey'] for output in stack['Outputs']]

                resources = self.cloudformation_list_stack_resources(profile_name=self.aws_profile, region_name=self.region,
                                                                     api_args={'StackName': self.stack})
                resources = [resource for resource in resources if not (resource['LogicalResourceId'] in parameter_keys or resource['LogicalResourceId'] in output_keys)]
                expanded[attr] = jinja.render({'template': template['TemplateBody'], 'stack': stack, 'resources': resources, 'indent': '    '})

                with open(getattr(self, attr), 'w+') as fh:
                    fh.write(expanded[attr])
                    fh.close()

            self.dlog('Deploying deck {} as {}'.format(getattr(self, 'deckspec'), self.deployment))
            farocli = FaroLibrary(aws_profile=self.sts_profile, region=self.region, logger=self._LOGGER)
            farocli.build_local_deckspec(self.deckspec)
            deckfile = farocli.get_deck_file()
            deck, version = farocli.get_name_and_version()
            self.vlog('Deploy deck {} as {}'.format(deck, self.deployment))
            if self.update:
                farocli.execute('deploy', '--localRepo', '--update', deck, self.deployment, '--version', version, '--parameterfile', self.parameters_file)
            else:
                farocli.execute('deploy', '--localRepo', deck, self.deployment, '--version', version, '--parameterfile', self.parameters_file)

            self.check_deployment(first=False)

# end TDCCLIContext

pass_context = click.decorators.make_pass_decorator(TDCCLIContext, ensure=True)
