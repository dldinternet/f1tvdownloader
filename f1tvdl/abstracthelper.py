import abc
import six


@six.add_metaclass(abc.ABCMeta)
class AbstractHelper(object):

    def __getattr__(self, item):
        method = getattr(self._context, item, None)
        if method:
            return method
        raise AttributeError(item)

    @abc.abstractmethod
    def __init__(self, *args, **kwargs):
        if self.__class__.__name__ == AbstractHelper.__name__:
            raise Exception('Instantiation of abstract class')
        super(AbstractHelper, self).__init__(*args, **kwargs)
        self._cache = getattr(self, '_cache', {})
        self._context = kwargs.get('context', None)

    @property
    def ctx(self):
        return self._context

    @property
    def context(self):
        return self._context
