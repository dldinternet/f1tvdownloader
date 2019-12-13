import os

# noinspection PyUnresolvedReferences
from builtins import ModuleNotFoundError

from windsor.cli import set_commands_base, WindsorCLI

from tf.errors import TDCCommandNotFoundError

set_commands_base(os.path.dirname(__file__))


class TDCCLI(WindsorCLI):
	def get_command(self, ctx, name):
		try:
			return super(TDCCLI, self).get_command(ctx, name)
		except ModuleNotFoundError as exc:
			raise TDCCommandNotFoundError(exc)
