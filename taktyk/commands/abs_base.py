import abc


class AbsCommand(metaclass=abc.ABCMeta):
    @abc.abstractproperty
    def name(self):
        pass

    @abc.abstractmethod
    def execute(self, *args):
        pass


class NoCommand(AbsCommand):
    name = ''

    def execute(self, *args):
        pass
