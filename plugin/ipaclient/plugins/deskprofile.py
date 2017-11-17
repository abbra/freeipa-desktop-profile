from ipaclient.frontend import MethodOverride
from ipalib.parameters import File
from ipalib.plugable import Registry

register = Registry()


@register(override=True, no_fail=True)
class deskprofile_add(MethodOverride):
    def get_options(self):
        """
        Rewrite type for 'ipadeskdata' attribute to allow
        loading the content of JSON-formatted data from file
        """
        for opt in super(deskprofile_add, self).get_options():
            if opt.name == 'ipadeskdata' and self.env.interactive:
                opt = opt.clone_retype(opt.name, File)
            yield opt


@register(override=True, no_fail=True)
class deskprofile_mod(MethodOverride):
    def get_options(self):
        """
        Rewrite type for 'ipadeskdata' attribute to allow
        loading the content of JSON-formatted data from file
        """
        for opt in super(deskprofile_mod, self).get_options():
            if opt.name == 'ipadeskdata' and self.env.interactive:
                opt = opt.clone_retype(opt.name, File)
            yield opt
